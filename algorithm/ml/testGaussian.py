from math import e, sqrt, pi
import matplotlib.pyplot as plt
def gaussian(x, m=130,s=43):
    gauss = 1/(sqrt(2*pi)*s)*e**(-0.5*(float(x-m)/s)**2)
    return gauss
xs = []
ys = []
# percentage = 0
for i in range(1, 260):
    xs.append(i)
    ys.append(gaussian(i)*10000)
    # if i > 100 and i < 160:
        # percentage += gaussian(i)
# print("range 100-160:", percentage)
plt.plot(xs,ys)
plt.show()