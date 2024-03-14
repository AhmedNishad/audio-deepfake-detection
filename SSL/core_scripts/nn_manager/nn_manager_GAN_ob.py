#!/usr/bin/env python
"""
nn_manager_gan

A simple wrapper to run the training / testing process for GAN

"""
from __future__ import print_function

import time
import datetime
import numpy as np

import torch
import torch.nn as nn
import torch.nn.functional as F

import core_scripts.data_io.conf as nii_dconf
import core_scripts.other_tools.display as nii_display
import core_scripts.other_tools.str_tools as nii_str_tk
import core_scripts.op_manager.op_process_monitor as nii_monitor
import core_scripts.op_manager.op_display_tools as nii_op_display_tk
import core_scripts.nn_manager.nn_manager_tools as nii_nn_tools
import core_scripts.nn_manager.nn_manager_conf as nii_nn_manage_conf
import core_scripts.other_tools.debug as nii_debug


 

#############################################################

def f_run_one_epoch_GAN(
        args, pt_model_G, pt_model_D, 
        loss_wrapper, \
        device, monitor,  \
        data_loader, epoch_idx, 
        optimizer_G = None, optimizer_D = None, \
        target_norm_method = None):
    """
    f_run_one_epoch_GAN: 
       run one poech over the dataset (for training or validation sets)

    Args:
       args:         from argpase
       pt_model_G:   pytorch model (torch.nn.Module) generator
       pt_model_D:   pytorch model (torch.nn.Module) discriminator
       loss_wrapper: a wrapper over loss function
                     loss_wrapper.compute(generated, target) 
       device:       torch.device("cuda") or torch.device("cpu")
       monitor:      defined in op_procfess_monitor.py
       data_loader:  pytorch DataLoader. 
       epoch_idx:    int, index of the current epoch
       optimizer_G:  torch optimizer or None, for generator
       optimizer_D:  torch optimizer or None, for discriminator
                     if None, the back propgation will be skipped
                     (for developlement set)
       target_norm_method: method to normalize target data
                           (by default, use pt_model.normalize_target)
    """
    # timer
    start_time = time.time()
        
    # loop over samples
    for data_idx, (data_in, data_tar, data_info, idx_orig) in \
        enumerate(data_loader):

        #############
        # prepare
        #############        
        # send data to device
        if optimizer_G is not None:
            optimizer_G.zero_grad()
        if optimizer_D is not None:
            optimizer_D.zero_grad()
            
        # normalize the target data (for input for discriminator)
        if isinstance(data_tar, torch.Tensor):
            data_tar = data_tar.to(device, dtype=nii_dconf.d_dtype)
            # there is no way to normalize the data inside loss
            # thus, do normalization here
            if target_norm_method is None:
                normed_target = pt_model_G.normalize_target(data_tar)
            else:
                normed_target = target_norm_method(data_tar)
        else:
            nii_display.f_die("target data is required")

        # to device (we assume noise will be generated by the model itself)
        # here we only provide external condition
        data_in = data_in.to(device, dtype=nii_dconf.d_dtype)
        
        ############################
        # Update Discriminator
        ############################        
        ####
        # train with real
        ####
        pt_model_D.zero_grad()
        d_out_real = pt_model_D(data_tar, data_in)
        errD_real = loss_wrapper.compute_gan_D_real(d_out_real)
        if optimizer_D is not None:
            errD_real.backward()

        # this should be given by pt_model_D or loss wrapper
        #d_out_real_mean = d_out_real.mean()

        ###
        # train with fake
        ###
        #  generate sample
        if args.model_forward_with_target:
            # if model.forward requires (input, target) as arguments
            # for example, for auto-encoder & autoregressive model
            if isinstance(data_tar, torch.Tensor):
                data_tar_tm = data_tar.to(device, dtype=nii_dconf.d_dtype)
                if args.model_forward_with_file_name:
                    data_gen = pt_model_G(data_in, data_tar_tm, data_info)
                else:
                    data_gen = pt_model_G(data_in, data_tar_tm)
            else:
                nii_display.f_print("--model-forward-with-target is set")
                nii_display.f_die("but data_tar is not loaded")
        else:
            if args.model_forward_with_file_name:
                # specifcal case when model.forward requires data_info
                data_gen = pt_model_G(data_in, data_info)
            else:
                # normal case for model.forward(input)
                data_gen = pt_model_G(data_in)
            
        # data_gen.detach() is required
        #  https://github.com/pytorch/examples/issues/116
        #  https://stackoverflow.com/questions/46774641/
        d_out_fake = pt_model_D(data_gen.detach(), data_in)
        errD_fake = loss_wrapper.compute_gan_D_fake(d_out_fake)
        if optimizer_D is not None:
            errD_fake.backward()

        # get the summed error for discrminator (only for displaying)
        errD = errD_real + errD_fake
        
        # update discriminator weight
        if optimizer_D is not None:
            optimizer_D.step()

        ############################
        # Update Generator 
        ############################
        pt_model_G.zero_grad()
        d_out_fake_for_G = pt_model_D(data_gen, data_in)
        errG_gan = loss_wrapper.compute_gan_G(d_out_fake_for_G)

        # if defined, calculate auxilliart loss
        if hasattr(loss_wrapper, "compute_aux"):
            errG_aux = loss_wrapper.compute_aux(data_gen, data_tar)
        else:
            errG_aux = torch.zeros_like(errG_gan)

        # if defined, calculate feat-matching loss
        if hasattr(loss_wrapper, "compute_feat_match"):
            errG_feat = loss_wrapper.compute_feat_match(
                d_out_real, d_out_fake_for_G)
        else:
            errG_feat = torch.zeros_like(errG_gan)

        # sum loss for generator
        errG = errG_gan + errG_aux + errG_feat

        if optimizer_G is not None:
            errG.backward()
            optimizer_G.step()
        
        # construct the loss for logging and early stopping 
        # only use errG_aux for early-stopping
        loss_computed = [
            [errG_aux, errD_real, errD_fake, errG_gan, errG_feat],
            [True, False, False, False, False]]
        
        # to handle cases where there are multiple loss functions
        _, loss_vals, loss_flags = nii_nn_tools.f_process_loss(loss_computed)
                    
        # save the training process information to the monitor
        end_time = time.time()
        batchsize = len(data_info)
        for idx, data_seq_info in enumerate(data_info):
            # loss_value is supposed to be the average loss value
            # over samples in the the batch, thus, just loss_value
            # rather loss_value / batchsize
            monitor.log_loss(loss_vals, loss_flags, \
                             (end_time-start_time) / batchsize, \
                             data_seq_info, idx_orig.numpy()[idx], \
                             epoch_idx)
            # print infor for one sentence
            if args.verbose == 1:
                monitor.print_error_for_batch(data_idx*batchsize + idx,\
                                              idx_orig.numpy()[idx], \
                                              epoch_idx)
            # 
        # start the timer for a new batch
        start_time = time.time()
            
    # lopp done
    return

def f_run_one_epoch_WGAN(
        args, pt_model_G, pt_model_D, 
        loss_wrapper, \
        device, monitor,  \
        data_loader, epoch_idx, 
        optimizer_G = None, optimizer_D = None, \
        target_norm_method = None):
    """
    f_run_one_epoch_WGAN: 
       similar to f_run_one_epoch_GAN, but for WGAN
    """
    # timer
    start_time = time.time()
    
    # This should be moved to model definition
    # number of critic (default 5)
    num_critic = 5
    # clip value
    wgan_clamp = 0.01

    # loop over samples
    for data_idx, (data_in, data_tar, data_info, idx_orig) in \
        enumerate(data_loader):
        
        # send data to device
        if optimizer_G is not None:
            optimizer_G.zero_grad()
        if optimizer_D is not None:
            optimizer_D.zero_grad()
            
        # prepare data
        if isinstance(data_tar, torch.Tensor):
            data_tar = data_tar.to(device, dtype=nii_dconf.d_dtype)
            # there is no way to normalize the data inside loss
            # thus, do normalization here
            if target_norm_method is None:
                normed_target = pt_model_G.normalize_target(data_tar)
            else:
                normed_target = target_norm_method(data_tar)
        else:
            nii_display.f_die("target data is required")

        # to device (we assume noise will be generated by the model itself)
        # here we only provide external condition
        data_in = data_in.to(device, dtype=nii_dconf.d_dtype)
        
        ############################
        # Update Discriminator
        ############################
        # train with real
        pt_model_D.zero_grad()
        d_out_real = pt_model_D(data_tar)
        errD_real = loss_wrapper.compute_gan_D_real(d_out_real)
        if optimizer_D is not None:
            errD_real.backward()
        d_out_real_mean = d_out_real.mean()

        # train with fake
        #  generate sample
        if args.model_forward_with_target:
            # if model.forward requires (input, target) as arguments
            # for example, for auto-encoder & autoregressive model
            if isinstance(data_tar, torch.Tensor):
                data_tar_tm = data_tar.to(device, dtype=nii_dconf.d_dtype)
                if args.model_forward_with_file_name:
                    data_gen = pt_model_G(data_in, data_tar_tm, data_info)
                else:
                    data_gen = pt_model_G(data_in, data_tar_tm)
            else:
                nii_display.f_print("--model-forward-with-target is set")
                nii_display.f_die("but data_tar is not loaded")
        else:
            if args.model_forward_with_file_name:
                # specifcal case when model.forward requires data_info
                data_gen = pt_model_G(data_in, data_info)
            else:
                # normal case for model.forward(input)
                data_gen = pt_model_G(data_in)
            
        # data_gen.detach() is required
        # https://github.com/pytorch/examples/issues/116
        d_out_fake = pt_model_D(data_gen.detach())
        errD_fake = loss_wrapper.compute_gan_D_fake(d_out_fake)
        if optimizer_D is not None:
            errD_fake.backward()
        d_out_fake_mean = d_out_fake.mean()
        
        errD = errD_real + errD_fake
        if optimizer_D is not None:
            optimizer_D.step()
            
        # clip weights of discriminator
        for p in pt_model_D.parameters():
            p.data.clamp_(-wgan_clamp, wgan_clamp)

        ############################
        # Update Generator 
        ############################
        pt_model_G.zero_grad()
        d_out_fake_for_G = pt_model_D(data_gen)
        errG_gan = loss_wrapper.compute_gan_G(d_out_fake_for_G)
        errG_aux = loss_wrapper.compute_aux(data_gen, data_tar)
        errG = errG_gan + errG_aux

        # only update after num_crictic iterations on discriminator
        if data_idx % num_critic == 0 and optimizer_G is not None:
            errG.backward()
            optimizer_G.step()
            
        d_out_fake_for_G_mean = d_out_fake_for_G.mean()
        
        # construct the loss for logging and early stopping 
        # only use errG_aux for early-stopping
        loss_computed = [[errG_aux, errG_gan, errD_real, errD_fake,
                          d_out_real_mean, d_out_fake_mean, 
                          d_out_fake_for_G_mean],
                         [True, False, False, False, False, False, False]]
        
        # to handle cases where there are multiple loss functions
        loss, loss_vals, loss_flags = nii_nn_tools.f_process_loss(loss_computed)

                    
        # save the training process information to the monitor
        end_time = time.time()
        batchsize = len(data_info)
        for idx, data_seq_info in enumerate(data_info):
            # loss_value is supposed to be the average loss value
            # over samples in the the batch, thus, just loss_value
            # rather loss_value / batchsize
            monitor.log_loss(loss_vals, loss_flags, \
                             (end_time-start_time) / batchsize, \
                             data_seq_info, idx_orig.numpy()[idx], \
                             epoch_idx)
            # print infor for one sentence
            if args.verbose == 1:
                monitor.print_error_for_batch(data_idx*batchsize + idx,\
                                              idx_orig.numpy()[idx], \
                                              epoch_idx)
            # 
        # start the timer for a new batch
        start_time = time.time()
            
    # lopp done
    return


def f_train_wrapper_GAN(
        args, pt_model_G, pt_model_D, loss_wrapper, device, \
        optimizer_G_wrapper, optimizer_D_wrapper, \
        train_dataset_wrapper, \
        val_dataset_wrapper = None, \
        checkpoint_G = None, checkpoint_D = None):
    """ 
    f_train_wrapper_GAN(
       args, pt_model_G, pt_model_D, loss_wrapper, device, 
       optimizer_G_wrapper, optimizer_D_wrapper, 
       train_dataset_wrapper, val_dataset_wrapper = None,
       check_point = None):

      A wrapper to run the training process

    Args:
       args:         argument information given by argpase
       pt_model_G:   generator, pytorch model (torch.nn.Module)
       pt_model_D:   discriminator, pytorch model (torch.nn.Module)
       loss_wrapper: a wrapper over loss functions
                     loss_wrapper.compute_D_real(discriminator_output) 
                     loss_wrapper.compute_D_fake(discriminator_output) 
                     loss_wrapper.compute_G(discriminator_output)
                     loss_wrapper.compute_G(fake, real)
       device:       torch.device("cuda") or torch.device("cpu")

       optimizer_G_wrapper: 
           a optimizer wrapper for generator (defined in op_manager.py)
       optimizer_D_wrapper: 
           a optimizer wrapper for discriminator (defined in op_manager.py)
       
       train_dataset_wrapper: 
           a wrapper over training data set (data_io/default_data_io.py)
           train_dataset_wrapper.get_loader() returns torch.DataSetLoader
       
       val_dataset_wrapper: 
           a wrapper over validation data set (data_io/default_data_io.py)
           it can None.
       
       checkpoint_G:
           a check_point that stores every thing to resume training

       checkpoint_D:
           a check_point that stores every thing to resume training
    """        
    
    nii_display.f_print_w_date("Start model training")

    ##############
    ## Preparation
    ##############

    # get the optimizer
    optimizer_G_wrapper.print_info()
    optimizer_D_wrapper.print_info()
    optimizer_G = optimizer_G_wrapper.optimizer
    optimizer_D = optimizer_D_wrapper.optimizer
    epoch_num = optimizer_G_wrapper.get_epoch_num()
    no_best_epoch_num = optimizer_G_wrapper.get_no_best_epoch_num()
    
    # get data loader for training set
    train_dataset_wrapper.print_info()
    train_data_loader = train_dataset_wrapper.get_loader()
    train_seq_num = train_dataset_wrapper.get_seq_num()

    # get the training process monitor
    monitor_trn = nii_monitor.Monitor(epoch_num, train_seq_num)

    # if validation data is provided, get data loader for val set
    if val_dataset_wrapper is not None:
        val_dataset_wrapper.print_info()
        val_data_loader = val_dataset_wrapper.get_loader()
        val_seq_num = val_dataset_wrapper.get_seq_num()
        monitor_val = nii_monitor.Monitor(epoch_num, val_seq_num)
    else:
        monitor_val = None

    # training log information
    train_log = ''
    model_tags = ["_G", "_D"]

    # prepare for DataParallism if available
    # pytorch.org/tutorials/beginner/blitz/data_parallel_tutorial.html
    if torch.cuda.device_count() > 1 and args.multi_gpu_data_parallel:
        nii_display.f_die("data_parallel not implemented for GAN")
    else:
        nii_display.f_print("\nUse single GPU: %s\n" % \
                            (torch.cuda.get_device_name(device)))
        flag_multi_device = False
        normtarget_f = None

    pt_model_G.to(device, dtype=nii_dconf.d_dtype)
    pt_model_D.to(device, dtype=nii_dconf.d_dtype)

    # print the network    
    nii_display.f_print("Setup generator")
    nii_nn_tools.f_model_show(pt_model_G, model_type='GAN')
    nii_display.f_print("Setup discriminator")
    nii_nn_tools.f_model_show(pt_model_D, do_model_def_check=False,
                              model_type='GAN')
    nii_nn_tools.f_loss_show(loss_wrapper, model_type='GAN')

    ###############################
    ## Resume training if necessary
    ###############################

    # resume training or initialize the model if necessary
    cp_names = nii_nn_manage_conf.CheckPointKey()
    if checkpoint_G is not None or checkpoint_D is not None:
        for checkpoint, optimizer, pt_model, model_name in \
            zip([checkpoint_G, checkpoint_D], [optimizer_G, optimizer_D], 
                [pt_model_G, pt_model_D], ["Generator", "Discriminator"]):
            nii_display.f_print("For %s" % (model_name))
            if type(checkpoint) is dict:
                # checkpoint
                # load model parameter and optimizer state
                if cp_names.state_dict in checkpoint:
                    # wrap the state_dic in f_state_dict_wrapper 
                    # in case the model is saved when DataParallel is on
                    pt_model.load_state_dict(
                        nii_nn_tools.f_state_dict_wrapper(
                            checkpoint[cp_names.state_dict], 
                            flag_multi_device))
                # load optimizer state
                if cp_names.optimizer in checkpoint:
                    optimizer.load_state_dict(checkpoint[cp_names.optimizer])
                # optionally, load training history
                if not args.ignore_training_history_in_trained_model:
                    #nii_display.f_print("Load ")
                    if cp_names.trnlog in checkpoint:
                        monitor_trn.load_state_dic(
                            checkpoint[cp_names.trnlog])
                    if cp_names.vallog in checkpoint and monitor_val:
                        monitor_val.load_state_dic(
                            checkpoint[cp_names.vallog])
                    if cp_names.info in checkpoint:
                        train_log = checkpoint[cp_names.info]
                    nii_display.f_print("Load check point, resume training")
                else:
                    nii_display.f_print("Load pretrained model and optimizer")
            elif checkpoint is not None:
                # only model status
                #pt_model.load_state_dict(checkpoint)
                pt_model.load_state_dict(
                    nii_nn_tools.f_state_dict_wrapper(
                        checkpoint, flag_multi_device))
                nii_display.f_print("Load pretrained model")
            else:
                nii_display.f_print("No pretrained model")
    # done for resume training

    ######################
    ### User defined setup 
    ######################
    # Not implemented yet

    ######################
    ### Start training
    ######################

    # other variables
    flag_early_stopped = False
    start_epoch = monitor_trn.get_epoch()
    epoch_num = monitor_trn.get_max_epoch()

    # select one wrapper, based on the flag in loss definition
    if hasattr(loss_wrapper, "flag_wgan") and loss_wrapper.flag_wgan:
        f_wrapper_gan_one_epoch = f_run_one_epoch_WGAN
    else:
        f_wrapper_gan_one_epoch = f_run_one_epoch_GAN

    # print
    _ = nii_op_display_tk.print_log_head()
    nii_display.f_print_message(train_log, flush=True, end='')
        
    
    # loop over multiple epochs
    for epoch_idx in range(start_epoch, epoch_num):

        # training one epoch
        pt_model_D.train()
        pt_model_G.train()
        
        f_wrapper_gan_one_epoch(
            args, pt_model_G, pt_model_D, 
            loss_wrapper, device, \
            monitor_trn, train_data_loader, \
            epoch_idx, optimizer_G, optimizer_D, 
            normtarget_f)

        time_trn = monitor_trn.get_time(epoch_idx)
        loss_trn = monitor_trn.get_loss(epoch_idx)
        
        # if necessary, do validataion 
        if val_dataset_wrapper is not None:
            # set eval() if necessary 
            if args.eval_mode_for_validation:
                pt_model_G.eval()
                pt_model_D.eval()
            with torch.no_grad():
                f_wrapper_gan_one_epoch(
                    args, pt_model_G, pt_model_D, 
                    loss_wrapper, \
                    device, \
                    monitor_val, val_data_loader, \
                    epoch_idx, None, None, normtarget_f)
            time_val = monitor_val.get_time(epoch_idx)
            loss_val = monitor_val.get_loss(epoch_idx)
        else:
            time_val, loss_val = 0, 0
                
        
        if val_dataset_wrapper is not None:
            flag_new_best = monitor_val.is_new_best()
        else:
            flag_new_best = True
            
        # print information
        train_log += nii_op_display_tk.print_train_info(
            epoch_idx, time_trn, loss_trn, time_val, loss_val, 
            flag_new_best, optimizer_G_wrapper.get_lr_info())

        # save the best model
        if flag_new_best:
            for pt_model, tmp_tag in zip([pt_model_G, pt_model_D], model_tags):
                tmp_best_name = nii_nn_tools.f_save_trained_name(args, tmp_tag)
                torch.save(pt_model.state_dict(), tmp_best_name)
            
        # save intermediate model if necessary
        if not args.not_save_each_epoch:
            # save model discrminator and generator
            for pt_model, optimizer, model_tag in \
                zip([pt_model_G, pt_model_D], [optimizer_G, optimizer_D], 
                    model_tags):

                tmp_model_name = nii_nn_tools.f_save_epoch_name(
                    args, epoch_idx, model_tag)
                if monitor_val is not None:
                    tmp_val_log = monitor_val.get_state_dic()
                else:
                    tmp_val_log = None
                # save
                tmp_dic = {
                    cp_names.state_dict : pt_model.state_dict(),
                    cp_names.info : train_log,
                    cp_names.optimizer : optimizer.state_dict(),
                    cp_names.trnlog : monitor_trn.get_state_dic(),
                    cp_names.vallog : tmp_val_log
                }
                torch.save(tmp_dic, tmp_model_name)
                if args.verbose == 1:
                    nii_display.f_eprint(str(datetime.datetime.now()))
                    nii_display.f_eprint("Save {:s}".format(tmp_model_name),
                                         flush=True)
        
        # early stopping
        if monitor_val is not None and \
           monitor_val.should_early_stop(no_best_epoch_num):
            flag_early_stopped = True
            break
        
    # loop done        

    nii_op_display_tk.print_log_tail()
    if flag_early_stopped:
        nii_display.f_print("Training finished by early stopping")
    else:
        nii_display.f_print("Training finished")
    nii_display.f_print("Model is saved to", end = '')
    for model_tag in model_tags:
        nii_display.f_print("{}".format(
            nii_nn_tools.f_save_trained_name(args, model_tag)))
    return

             
if __name__ == "__main__":
    print("nn_manager for GAN")
