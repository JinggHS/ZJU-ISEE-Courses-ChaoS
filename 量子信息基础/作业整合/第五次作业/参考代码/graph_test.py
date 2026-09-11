import numpy as np
import matplotlib.pyplot as plt

x = np.linspace(-5, 5, 200)
y = x * np.sin(x)

plt.plot(x, y)
plt.xlabel("x")
plt.ylabel("y")
plt.title("y = x sin(x)")
plt.grid()

plt.show()