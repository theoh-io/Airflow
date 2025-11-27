/*--------------------------------*- C++ -*----------------------------------*\
| =========                 |                                                 |
| \\      /  F ield         | microClimateFoam - Field Creation              |
|  \\    /   O peration     |                                                 |
|   \\  /    A nd           |                                                 |
|    \\/     M anipulation  |                                                 |
\*---------------------------------------------------------------------------*/

Info<< "Reading field U\n" << endl;
volVectorField U
(
    IOobject
    (
        "U",
        runTime.timeName(),
        mesh,
        IOobject::MUST_READ,
        IOobject::AUTO_WRITE
    ),
    mesh
);

Info<< "Reading field p\n" << endl;
volScalarField p
(
    IOobject
    (
        "p",
        runTime.timeName(),
        mesh,
        IOobject::MUST_READ,
        IOobject::AUTO_WRITE
    ),
    mesh
);

#include "createPhi.H"

label pRefCell = 0;
scalar pRefValue = 0.0;
setRefCell(p, mesh.solutionDict().subDict("PISO"), pRefCell, pRefValue);

Info<< "Reading transportProperties\n" << endl;
IOdictionary transportProperties
(
    IOobject
    (
        "transportProperties",
        runTime.constant(),
        mesh,
        IOobject::MUST_READ_IF_MODIFIED,
        IOobject::NO_WRITE
    )
);

const dimensionedScalar nu("nu", dimViscosity, transportProperties);

Info<< "Reading field T\n" << endl;
volScalarField T
(
    IOobject
    (
        "T",
        runTime.timeName(),
        mesh,
        IOobject::MUST_READ,
        IOobject::AUTO_WRITE
    ),
    mesh
);

// Thermal properties for Boussinesq buoyancy
const dimensionedScalar rhoRef("rhoRef", dimDensity, transportProperties);
const dimensionedScalar beta("beta", dimless/dimTemperature, transportProperties);
const dimensionedScalar TRef("TRef", dimTemperature, transportProperties);
const dimensionedVector g("g", dimAcceleration, transportProperties);

// Thermal diffusivity (alpha = k/(rho*Cp), simplified as constant for now)
const dimensionedScalar alpha("alpha", dimViscosity, transportProperties);

Info<< "Thermal properties:" << nl
    << "    rhoRef = " << rhoRef.value() << " kg/m³" << nl
    << "    beta   = " << beta.value() << " 1/K" << nl
    << "    TRef   = " << TRef.value() << " K" << nl
    << "    alpha  = " << alpha.value() << " m²/s" << nl
    << "    g      = " << g.value() << " m/s²" << endl;

// Continuity error tracking
scalar cumulativeContErr = 0.0;

