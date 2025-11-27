/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | microClimateFoam - Pressure Equation           |
|  \\    /   O peration     |                                                 |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/

// Non-orthogonal pressure corrector loop
for (int nonOrth = 0; nonOrth <= mesh.solutionDict().subDict("PISO").lookupOrDefault<int>("nNonOrthogonalCorrectors", 0); nonOrth++)
{
    fvScalarMatrix pEqn
    (
        fvm::laplacian(rAU, p) == fvc::div(phiHbyA)
    );

    pEqn.setReference(pRefCell, pRefValue);
    pEqn.solve();

    if (nonOrth == 0)
    {
        phi = phiHbyA - pEqn.flux();
    }
    else
    {
        phi -= pEqn.flux();
    }
}

#include "continuityErrs.H"

// Explicitly relax pressure for momentum corrector
if (mesh.solutionDict().found("relaxationFactors"))
{
    if (mesh.solutionDict().subDict("relaxationFactors").found("fields"))
    {
        p.storePrevIter();
        p.relax(mesh.solutionDict().subDict("relaxationFactors").subDict("fields").lookupOrDefault<scalar>("p", 1.0));
    }
}

// Correct velocity
U = HbyA - rAU*fvc::grad(p);
U.correctBoundaryConditions();

