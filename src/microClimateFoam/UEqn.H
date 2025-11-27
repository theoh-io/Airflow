/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | microClimateFoam - Momentum Equation           |
|  \\    /   O peration     |                                                 |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/

// Solve the momentum equation
fvVectorMatrix UEqn
(
    fvm::ddt(U)
  + fvm::div(phi, U)
  - fvm::laplacian(nu, U)
);

UEqn.relax();

if (mesh.solutionDict().found("relaxationFactors"))
{
    if (mesh.solutionDict().subDict("relaxationFactors").found("equations"))
    {
        UEqn.relax(mesh.solutionDict().subDict("relaxationFactors").subDict("equations").lookupOrDefault<scalar>("U", 1.0));
    }
}

volScalarField rAU(1.0/UEqn.A());
volVectorField HbyA(constrainHbyA(rAU*UEqn.H(), U, p));
surfaceScalarField phiHbyA("phiHbyA", fvc::flux(HbyA));

adjustPhi(phiHbyA, U, p);

// Update the pressure BCs to ensure flux consistency
constrainPressure(p, U, phiHbyA, rAU);

