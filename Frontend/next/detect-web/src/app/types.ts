export interface DetectionResult{
    _id: MongoId;
    publicFigure?: string;
    transcript: string;
    createdOn?: MongoDate;
    fileName: string;
}

export interface DetectionResponse{
    _id: string;
    isDeepfake: boolean;
}

export interface MongoDate{
    $date: Date;
}

export interface MongoId{
    $oid: string;
}