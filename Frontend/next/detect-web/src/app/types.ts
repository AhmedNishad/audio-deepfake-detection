export interface DetectionResult{
    _id: string;
    publicFigure?: string;
    transcript: string;
    createdOn?: Date;
}

export interface DetectionResponse{
    _id: string;
    isDeepfake: boolean;
}