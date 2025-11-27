/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | microClimateFoam - Courant Number              |
|  \\    /   O peration     |                                                 |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/

{
    scalar CoNum = 0.0;
    scalar meanCoNum = 0.0;

    if (mesh.nInternalFaces())
    {
        surfaceScalarField SfUfbyDelta =
            mesh.surfaceInterpolation::deltaCoeffs()*mag(phi);

        CoNum = max(SfUfbyDelta/mesh.magSf())
            .value()*runTime.deltaTValue();

        meanCoNum = (sum(SfUfbyDelta)/sum(mesh.magSf()))
            .value()*runTime.deltaTValue();
    }

    Info<< "Courant Number mean: " << meanCoNum
        << " max: " << CoNum << endl;
}

