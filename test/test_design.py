"""Tests for the design module"""
import numpy as np
import compflow as cf
from turbigen.design import *
from turbigen.design import _integrate_length

# Set up test data

# Ranges of velocity triangle parameters covering the classic Smith chart
phi = np.linspace(0.4, 1.2, 7)
psi = np.linspace(0.8, 2.4, 7)

# "Reasonable" range of reaction (usually close to Lam = 0.5 in gas turbines)
# Known limitation: does not converge for very high reaction Lam > 0.8
Lam = np.linspace(0.3, 0.7, 5)

# Other parameters
Al1 = 10.0
Ma2 = 0.6
ga = 1.33
eta = 0.9
Lam_ref = 0.5
Al_range = np.linspace(-30.0, 30.0, 11)

Ma_low = 0.01
eta_ideal = 1.0

# Begin test functions


def test_Zweifel():
    """Verify Zweifel pitch-to-chord for low-speed lossless repeating stages."""
    for phii in phi:
        for psii in psi:
            for Al1i in Al_range:
                Alnow = (Al1i, Al1i)  # Same inlet and exit angle
                stg = nondim_stage_from_Al(phii, psii, Alnow, Ma_low, ga, eta_ideal)

                # Evaluate Zweifel using built in function
                Z = 0.8
                s_c_out = np.array(pitch_Zweifel(stg, (Z, Z)))

                # Evaluate low-speed lossless approximation
                Alr = np.radians(stg.Al)
                s_c_stator = (
                    Z
                    / 2.0
                    / (np.cos(Alr[1]) ** 2.0)
                    / (np.tan(Alr[1]) - np.tan(Alr[0]))
                )
                Alrelr = np.radians(stg.Alrel)
                s_c_rotor = (
                    Z
                    / 2.0
                    / (np.cos(Alrelr[2]) ** 2.0)
                    / np.abs(np.tan(Alrelr[2]) - np.tan(Alrelr[1]))
                )

                # Check that the two are within a tolerance
                assert np.all(
                    np.abs(s_c_out - np.array((s_c_stator, s_c_rotor))) < 1e-4
                )


def test_circulation_coeff():
    """Verify circulation pitch-to-chord for low-speed lossless repeating stages."""
    for phii in phi:
        for psii in psi:
            for Al1i in Al_range:
                Alnow = (Al1i, Al1i)  # Same inlet and exit angle
                stg = nondim_stage_from_Al(phii, psii, Alnow, Ma_low, ga, eta_ideal)

                # Evaluate Zweifel using built in function
                C0 = 0.65
                s_c_out = np.array(pitch_circulation(stg, C0))
                print(s_c_out)

                # Evaluate low-speed lossless approximation
                Alr = np.radians(stg.Al[:2])
                s_c_stator = (
                    C0
                    * _integrate_length(Alr)
                    / np.cos(Alr[1])
                    / np.abs(np.tan(Alr[0]) - np.tan(Alr[1]))
                )
                Alrelr = np.radians(stg.Alrel[1:])
                s_c_rotor = (
                    C0
                    * _integrate_length(Alrelr)
                    / np.cos(Alrelr[1])
                    / np.abs(np.tan(Alrelr[0]) - np.tan(Alrelr[1]))
                )
                print((s_c_stator, s_c_rotor))

                # Check that the two are within a tolerance
                assert np.all(
                    np.abs(s_c_out - np.array((s_c_stator, s_c_rotor))) < 1e-4
                )


def test_repeating():
    """Verify analytically some repeating stage velocity triangles."""
    for phii in phi:
        for psii in psi:
            for Al1i in Al_range:
                Alnow = (Al1i, Al1i)  # Same inlet and exit angle
                stg = nondim_stage_from_Al(phii, psii, Alnow, Ma2, ga, eta)
                psi_out = 2.0 * (1.0 - stg.Lam - phii * np.tan(np.radians(Al1i)))
                assert np.isclose(psii, psi_out)


def test_mass():
    """Check for mass conservation."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(
                    phii, psii, Lami, Al1, Ma2, ga, eta, Vx_rat=(0.9, 1.2)
                )
                mdot_out = (
                    cf.mcpTo_APo_from_Ma(stg.Ma, ga)
                    * stg.Ax_Ax1
                    * stg.Po_Po1
                    * np.cos(np.radians(stg.Al))
                    / np.sqrt(stg.To_To1)
                )
                assert np.isclose(*mdot_out)


def test_Lam():
    """Check target reaction is achieved by the yaw angle iteration."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(
                    phii, psii, Lami, Al1, Ma2, ga, eta, Vx_rat=(0.9, 1.2)
                )
                assert np.isclose(stg.Lam, Lami)


def test_Vx():
    """Verify that the axial velocity is as required."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(
                    phii, psii, Lami, Al1, Ma2, ga, eta, Vx_rat=(0.9, 1.2)
                )
                V_cpTo = cf.V_cpTo_from_Ma(stg.Ma, ga) * np.sqrt(stg.To_To1)
                Vx_cpTo = V_cpTo * np.cos(np.radians(stg.Al))
                Vx_U = Vx_cpTo / stg.U_sqrt_cpTo1
                Vx_rat_out = Vx_U / phii
                assert np.all(np.isclose(Vx_rat_out, (0.9, 1.0, 1.2)))


def test_euler():
    """Verify that the Euler's work equation is satisfied."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(
                    phii, psii, Lami, Al1, Ma2, ga, eta, Vx_rat=(0.9, 1.2)
                )
                V_cpTo = cf.V_cpTo_from_Ma(stg.Ma, ga) * np.sqrt(stg.To_To1)
                Vt_cpTo = V_cpTo * np.sin(np.radians(stg.Al))
                Vt_U = Vt_cpTo / stg.U_sqrt_cpTo1
                dVt_U = Vt_U[1] - Vt_U[2]
                assert np.all(np.isclose(dVt_U, psii))


def test_loss():
    """Check that polytropic efficiency, loss coeffs and Po are correct."""
    for phii in phi:
        for psii in psi:
            for etai in [0.8, 0.9, 1.0]:
                stg = nondim_stage_from_Lam(phii, psii, Lam_ref, Al1, Ma2, ga, etai)
                # Check efficiency
                eta_out = (
                    np.log(stg.To_To1[-1]) / np.log(stg.Po_Po1[-1]) * ga / (ga - 1.0)
                )
                assert np.isclose(eta_out, etai)

                # Check loss coeffs
                # Note compressor definition using inlet dyn head
                Po2_Po1 = stg.Po_Po1[1]
                Po3_Po2_rel = (
                    cf.Po_P_from_Ma(stg.Marel[2], ga)
                    / cf.Po_P_from_Ma(stg.Marel[1], ga)
                    * cf.Po_P_from_Ma(stg.Ma[1], ga)
                    / cf.Po_P_from_Ma(stg.Ma[2], ga)
                    * stg.Po_Po1[2]
                    / stg.Po_Po1[1]
                )
                Po1_P1 = cf.Po_P_from_Ma(stg.Ma[0], ga)
                Po2_P2_rel = cf.Po_P_from_Ma(stg.Marel[1], ga)

                Yp_stator_out = (1.0 - Po2_Po1) / (1.0 - 1.0 / Po1_P1)
                assert np.isclose(Yp_stator_out, stg.Yp[0])
                Yp_rotor_out = (1.0 - Po3_Po2_rel) / (1.0 - 1.0 / Po2_P2_rel)
                assert np.isclose(Yp_rotor_out, stg.Yp[1])


def test_psi():
    """Check that stage loading coefficient is correct."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(phii, psii, Lami, Al1, Ma2, ga, eta)
                psi_out = (1.0 - stg.To_To1[2]) / stg.U_sqrt_cpTo1 ** 2.0
                assert np.isclose(psii, psi_out)


def test_Al():
    """Check that inlet and exit yaw angles are as specified."""
    for phii in phi:
        for psii in psi:
            for Al1i in Al_range:
                for Al3i in Al_range:
                    Alnow = (Al1i, Al3i)
                    stg = nondim_stage_from_Al(phii, psii, Alnow, Ma2, ga, eta)
                    assert np.all(
                        np.isclose(
                            np.array(stg.Al)[
                                (0, 2),
                            ],
                            Alnow,
                        )
                    )


def test_valid():
    """Check that output data is always physically sensible."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(phii, psii, Lami, Al1, Ma2, ga, eta)
                # No nans or infinities
                for xi in stg:
                    assert np.all(np.isfinite(xi))
                # All variables excluding flow angles should be non-negative
                for vi, xi in stg._asdict().items():
                    if vi not in ["Al", "Alrel", "Vt_U", "Vtrel_U"]:
                        assert np.all(np.array(xi) >= 0.0)
                # Flow angles less than 90 degrees
                for vi in ["Al", "Alrel"]:
                    assert np.all(np.abs(getattr(stg, vi)) < 90.0)
                # No diverging annuli (for these designs Vx=const)
                assert np.all(np.array(stg.Ax_Ax1) >= 1.0)


def test_annulus():
    """Ensure that annulus lines are created successfully."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:
                stg = nondim_stage_from_Lam(phii, psii, Lami, Al1, Ma2, ga, eta)
                htr = 0.9
                cpTo1 = 1.0e6
                Omega = 2.0 * np.pi * 50.0
                rm, Dr = annulus_line(stg, htr, cpTo1, Omega)

                # Basic validity checks
                assert np.all(rm > 0.0)
                assert np.all(Dr > 0.0)
                assert np.all(rm > Dr)

                # Verify that U/sqrt(cpTo1) is correct
                U = Omega * rm
                assert np.isclose(stg.U_sqrt_cpTo1, U / np.sqrt(cpTo1))

                # Verify hub-to-tip ratio
                rt = rm + Dr[1] / 2.0
                rh = rm - Dr[1] / 2.0
                assert np.isclose(htr, rh / rt)


def test_chord():
    """Verify chord calculation with incompressible cases."""

    To1 = 300.0
    mu = muref * (To1 / Tref) ** expon
    cp = 1150.0
    rgas = cp / ga * (ga - 1)
    cpTo1 = cp * To1
    Po1 = 1.0e5
    Re = 4e3
    tol = Re * 0.001

    for phii in phi:
        for psii in psi:
            for Al1i in Al_range:
                Alnow = (Al1i, Al1i)  # Same inlet and exit angle
                stg = nondim_stage_from_Al(phii, psii, Alnow, Ma_low, ga, eta_ideal)
                cx = chord_from_Re(stg, Re, cpTo1, Po1, rgas)
                V2 = compflow.V_cpTo_from_Ma(stg.Ma[1], ga) * np.sqrt(cpTo1)
                rho2 = Po1 / rgas / To1
                Re_out = rho2 * V2 * cx / mu
                assert np.abs(Re - Re_out) < tol


def test_section():
    """Verify that blade sections are generated successfully."""
    chi1 = np.arange(-30.0, 30.0, 7)
    chi2 = np.arange(-60.0, 60.0, 7)
    aft = np.arange(-1.0, 1.0, 11)
    for chi1i in chi1:
        for chi2i in chi2:
            for afti in aft:
                xy = blade_section([chi1i, chi2i], afti)

                # Streamwise coordinate goes in correct direction
                assert np.all(np.diff(xy[0, :], 1) > 0.0)

                # Upper surface is higher than lower surface
                assert np.all(xy[1, :] - xy[2, :] >= 0.0)

                # Surfaces meet at ends
                assert np.all(np.isclose(xy[1, (0, -1)], xy[2, (0, -1)]))

                # Check camber line angles
                yc = np.mean(xy[(1, 2), :], axis=0)
                dyc = np.diff(yc, 1)
                dxc = np.diff(xy[0, :], 1)
                ang = np.degrees(np.arctan2(dyc, dxc))[
                    (0, -1),
                ]
                ang_tol = 0.1
                assert np.all(np.abs(ang - (chi1i, chi2i)) < ang_tol)


def test_free_vortex():
    """Verify that vortex distributions have constant angular momentum."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:

                # Generate stage with annulus line
                stg = nondim_stage_from_Lam(phii, psii, Lami, Al1, Ma2, ga, eta)
                htr = 0.9
                cpTo1 = 1.0e6
                Omega = 2.0 * np.pi * 50.0
                rm, Dr = annulus_line(stg, htr, cpTo1, Omega)

                # Make radius ratios
                rh = rm - Dr / 2.0
                rc = rm + Dr / 2.0
                r_rm = (
                    np.stack([np.linspace(rhi, rci, 20) for rhi, rci in zip(rh, rc)])
                    / rm
                )

                # Run through the free-vortex functions with no deviation
                chi_vane, chi_blade = free_vortex(stg, r_rm, (0.0, 0.0))

                # Check angular momentum is constant to within tolerance
                tol = 1e-10
                mom_vane = r_rm[:2, :] * np.tan(np.radians(chi_vane))
                assert np.all(np.ptp(mom_vane, axis=1) < tol)
                mom_blade = r_rm[2:, :] * (
                    r_rm[2:, :] / stg.phi + np.tan(np.radians(chi_blade))
                )
                assert np.all(np.ptp(mom_blade, axis=1) < tol)


def test_deviation():
    """Verify that deviation goes in the correct direction."""
    for phii in phi:
        for psii in psi:
            for Lami in Lam:

                # Generate stage with annulus line
                stg = nondim_stage_from_Lam(phii, psii, Lami, Al1, Ma2, ga, eta)
                htr = 0.9
                cpTo1 = 1.0e6
                Omega = 2.0 * np.pi * 50.0
                rm, Dr = annulus_line(stg, htr, cpTo1, Omega)

                # Make radius ratios
                rh = rm - Dr / 2.0
                rc = rm + Dr / 2.0
                r_rm = (
                    np.stack([np.linspace(rhi, rci, 20) for rhi, rci in zip(rh, rc)])
                    / rm
                )

                # Loop over deviations
                dev = [0.0, 1.0]
                chi_all = np.stack(
                    [free_vortex(stg, r_rm, (devi, devi)) for devi in dev]
                )
                chi_vane = chi_all[:, 0, :, :]
                chi_blade = chi_all[:, 1, :, :]

                # Our sign conventions mean that turning is
                # +ve through vane, -ve through rotor
                # So more deviation should mean that outlet flow angle
                # reduces for vane, increases for rotor
                # But we aim to counteract this effect by moving metal
                # So with more deviation, the metal angle must
                # increase for vane, decrease for blade
                assert np.all(
                    np.isclose(np.diff(chi_vane[:, 1, :], 1, 0), np.diff(dev, 1))
                )
                assert np.all(
                    np.isclose(np.diff(chi_blade[:, 1, :], 1, 0), -np.diff(dev, 1))
                )
