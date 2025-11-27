#include "fvCFD.H"

int main(int argc, char *argv[])
{
    #include "setRootCase.H"
    #include "createTime.H"
    #include "createMesh.H"
    #include "createFields.H"

    #include "initContinuityErrs.H"

    Info<< "\nStarting time loop\n" << endl;

    while (runTime.loop())
    {
        Info<< "Time = " << runTime.timeName() << nl << endl;

        #include "CourantNo.H"

        // Pressure-velocity PISO corrector loop
        {
            #include "UEqn.H"
            
            // --- PISO loop
            for (int corr = 0; corr < mesh.solutionDict().subDict("PISO").lookupOrDefault<int>("nCorrectors", 2); corr++)
            {
                #include "pEqn.H"
            }
        }

        // Solve temperature transport equation
        #include "TEqn.H"

        runTime.write();

        Info<< "ExecutionTime = " << runTime.elapsedCpuTime() << " s"
            << "  ClockTime = " << runTime.elapsedClockTime() << " s"
            << nl << endl;
    }

    Info<< "End\n" << endl;
    return 0;
}

