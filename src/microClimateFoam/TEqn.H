/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | microClimateFoam - Temperature Equation         |
|  \\    /   O peration     |                                                 |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/

// Solve the temperature transport equation
fvScalarMatrix TEqn
(
    fvm::ddt(T)
  + fvm::div(phi, T)
  - fvm::laplacian(alpha, T)
);

TEqn.relax();

if (mesh.solutionDict().found("relaxationFactors"))
{
    if (mesh.solutionDict().subDict("relaxationFactors").found("equations"))
    {
        TEqn.relax(mesh.solutionDict().subDict("relaxationFactors").subDict("equations").lookupOrDefault<scalar>("T", 1.0));
    }
}

TEqn.solve();

