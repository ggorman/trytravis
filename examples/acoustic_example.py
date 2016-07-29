import numpy as np
from math import floor
from containers import IShot, IGrid
from Acoustic_codegen import Acoustic_cg

dimensions = (50, 50, 50)
model = IGrid()
model0 = IGrid()
model1 = IGrid()
model.shape = dimensions
model0.shape = dimensions
model1.shape = dimensions
origin = (0., 0.)
spacing = (20., 20.)
dtype = np.float32
t_order = 2
spc_order = 2


# Velocity models
def smooth10(vel, shape):
    out = np.ones(shape)
    out[:, :] = vel[:, :]
    nx = shape[0]
    for a in range(5, nx-6):
        out[a, :] = np.sum(vel[a - 5:a + 5, :], axis=0) / 10
    return out


# True velocity
true_vp = np.ones(dimensions) + 2.0
true_vp[:, :, int(dimensions[0] / 2):int(dimensions[0])] = 4.5

# Smooth velocity
initial_vp = smooth10(true_vp, dimensions)

dm_orig = true_vp**-2 - initial_vp**-2


def create_dm(dm):
    np.copyto(dm, dm_orig)

dv = -true_vp + initial_vp

model.create_model(origin, spacing, true_vp)

# Define seismic data.
data = IShot()

f0 = .010
dt = model.get_critical_dt()
t0 = 0.0
tn = 250.0;
nt = int(1+(tn-t0)/dt)
h = model.get_spacing()
data.reinterpolate(dt)


# Set up the source as Ricker wavelet for f0
def source(t, f0):
    r = (np.pi * f0 * (t - 1./f0))
    return (1-2.*r**2)*np.exp(-r**2)


time_series = source(np.linspace(t0, tn, nt), f0)
location = (origin[0] + dimensions[0] * spacing[0] * 0.5, 500,
            origin[1] + 2 * spacing[1])
data.set_source(time_series, dt, location)

receiver_coords = np.zeros((101, 3))
receiver_coords[:, 0] = np.linspace(50, 950, num=101)
receiver_coords[:, 1] = 500
receiver_coords[:, 2] = location[2]
data.set_receiver_pos(receiver_coords)
data.set_shape(nt, 101)
Acoustic = Acoustic_cg(model, data, dm_orig, None, nbpml = 10, t_order=2, s_order=2)
print("Preparing Forward")
print("Applying")
(rec, u) = Acoustic.Forward()

print("Preparing adjoint")
print("Applying")
(srca, v) = Acoustic.Adjoint(rec)

print("Preparing Gradient")
print("Applying")
g = Acoustic.Gradient(rec, u)

print("Preparing Born")
print("Applying")
LinRec = Acoustic.Born()
