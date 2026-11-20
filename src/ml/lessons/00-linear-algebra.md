# Linear algebra for machine learning

Almost every machine-learning algorithm in this track takes a table of numbers and does linear algebra on it.
Linear regression solves a linear system, PCA is a singular value decomposition, a neural network layer is
a matrix product followed by a nonlinearity, and k-NN and k-means compute distances between vectors.
You don't need a whole course in linear algebra. You do need to be fluent in about a dozen ideas and to
**see the shapes** of the arrays you work with. This lesson covers those ideas with numpy.

## 1. Data as a matrix

Müller & Guido use one convention throughout, and scikit-learn uses it too: a dataset is a matrix
$X \in \mathbb{R}^{n \times p}$.

- Each **row** $x_i \in \mathbb{R}^p$ is one *sample* (also called a data point or instance).
- Each **column** is one *feature*.
- Labels (targets) are a vector $y \in \mathbb{R}^n$, one entry per row.

The iris dataset, for example, is a $150 \times 4$ matrix: 150 flowers and 4 measurements per flower.

```python-run
import numpy as np
from sklearn.datasets import load_iris

iris = load_iris()
X, y = iris.data, iris.target
print("X shape:", X.shape, " y shape:", y.shape)
print("first sample (a row vector):", X[0])
print("first feature (a column):", X[:5, 0], "...")
print("feature names:", iris.feature_names)
```

> [!TIP]
> When code misbehaves, print `.shape` first. Most ML bugs come from shapes: a missing axis, a transpose,
> or a broadcast you didn't intend.

## 2. Vectors, the dot product and norms

A vector is an ordered list of numbers, and you can read it two ways: as a point in space, or as an arrow
from the origin. The **dot product** of two vectors of the same length is

$$a \cdot b = a^\top b = \sum_{j=1}^p a_j b_j = \lVert a\rVert\,\lVert b\rVert\cos\theta .$$

It measures how far two vectors point the same way. It is positive when they point in a similar direction,
zero when they are orthogonal (perpendicular), and negative when they point in opposite directions. A linear
model's prediction $\hat y = w^\top x + b$ is a dot product between a weight vector and a feature vector.

A **norm** measures the length of a vector:

| norm | formula | ML use |
|---|---|---|
| L2 (Euclidean) | $\lVert x\rVert_2 = \sqrt{\sum_j x_j^2}$ | distances in k-NN/k-means, ridge penalty |
| L1 (Manhattan) | $\lVert x\rVert_1 = \sum_j \lvert x_j\rvert$ | lasso penalty (makes weights sparse), MAE |
| L∞ | $\max_j \lvert x_j\rvert$ | adversarial robustness bounds |

The **Euclidean distance** between two samples is the norm of their difference, $\lVert a - b\rVert_2$.
The **cosine similarity** is $\frac{a\cdot b}{\lVert a\rVert\lVert b\rVert}$. Because it ignores length, it is
the standard similarity for text vectors and embeddings.

```python-run
import numpy as np
a = np.array([3.0, 4.0])
b = np.array([4.0, -3.0])
c = np.array([6.0, 8.0])
print("a.b =", a @ b, "(orthogonal)")
print("||a||_2 =", np.linalg.norm(a), " ||a||_1 =", np.linalg.norm(a, 1))
print("distance a-c =", np.linalg.norm(a - c))
cos = a @ c / (np.linalg.norm(a) * np.linalg.norm(c))
print("cosine(a, c) =", cos, "-> same direction, different length")
```

A useful identity: for unit vectors, $\lVert a-b\rVert^2 = 2 - 2\cos\theta$. After L2-normalising, ranking
by Euclidean distance and ranking by cosine similarity give the same order. Vector databases rely on this.

## 3. Matrices as linear maps

A matrix $W \in \mathbb{R}^{p\times q}$ turns a $p$-vector into a $q$-vector: $z = x^\top W$, or $z = W^\top x$
with column vectors. The rule for multiplying matrices is that **inner dimensions must match**:

$$\underbrace{A}_{n\times p}\ \underbrace{B}_{p\times q} = \underbrace{C}_{n\times q},\qquad C_{ik} = \sum_j A_{ij}B_{jk}.$$

Each entry of $C$ is the dot product of a row of $A$ with a column of $B$. Applying a model to a whole
dataset at once is a single matrix product. For a linear model, $\hat y = Xw + b$ gives $n$ predictions.
For a dense neural-network layer, $H = XW + b$ maps $n$ samples with $p$ features to $n$ samples with $q$
hidden units.

```python-run
import numpy as np
rng = np.random.RandomState(0)
X = rng.randn(5, 3)        # 5 samples, 3 features
W = rng.randn(3, 2)        # a layer mapping 3 -> 2
b = np.array([0.1, -0.1])  # one bias per output, broadcast over rows
H = X @ W + b
print("X", X.shape, "@ W", W.shape, "->", H.shape)
# the same thing, one sample at a time:
print(np.allclose(H[0], X[0] @ W + b))
```

Facts you will use constantly:

- $(AB)^\top = B^\top A^\top$.
- Matrix multiplication is associative but **not** commutative: in general $AB \ne BA$.
- The **identity** $I$ satisfies $AI = A$. An **inverse** $A^{-1}$ (square matrices only) satisfies
  $AA^{-1} = I$. In practice you almost never compute an inverse. You *solve* $Ax = b$ with
  `np.linalg.solve` or `lstsq`, which is faster and more accurate.
- **Broadcasting**: numpy stretches arrays of size 1 along an axis to match the other operand. `X - X.mean(axis=0)`
  centres every column, because the $(p,)$ mean vector is broadcast across the $n$ rows.

> [!WARNING]
> `A * B` in numpy multiplies **element-wise** (the Hadamard product $A\odot B$). For a matrix product
> use `A @ B`. Mixing them up is a classic silent bug when the shapes happen to be compatible, for example
> square matrices.

## 4. Rank, linear independence and least squares

The columns of $X$ are **linearly independent** if no column is a weighted sum of the others. The **rank**
is the number of independent columns. If two features are perfectly collinear (say temperature in °C and
in °F), the rank drops. The linear-regression system then has infinitely many solutions, and the
unregularised coefficients become unstable. Ridge regression fixes this by adding $\alpha I$, which makes
the system invertible.

Ordinary least squares minimises $\lVert y - Xw\rVert^2$. Setting the gradient to zero (next lesson) gives
the **normal equations**

$$X^\top X\,w = X^\top y .$$

Geometrically, $Xw$ is the point in the column space of $X$ that is closest to $y$. The residual
$y - Xw$ is orthogonal to every column, which is where the name "normal" comes from.

```python-run
import numpy as np
rng = np.random.RandomState(1)
X = np.hstack([np.ones((20, 1)), rng.randn(20, 2)])    # intercept column + 2 features
true_w = np.array([0.5, 2.0, -1.0])
y = X @ true_w + 0.1 * rng.randn(20)
w_normal = np.linalg.solve(X.T @ X, X.T @ y)
w_lstsq = np.linalg.lstsq(X, y, rcond=None)[0]
print("normal equations:", w_normal.round(3))
print("lstsq (SVD):     ", w_lstsq.round(3))
print("residual . columns ~ 0:", (X.T @ (y - X @ w_lstsq)).round(10))
```

## 5. Eigenvectors: directions a matrix only stretches

For a square matrix $A$, an **eigenvector** $v \neq 0$ satisfies $Av = \lambda v$: applying $A$ only
scales $v$, by the **eigenvalue** $\lambda$, and never rotates it. Symmetric matrices, such as covariance
matrices $C = \frac{1}{n-1}X_c^\top X_c$, have three good properties:

- all eigenvalues are real, and for covariance matrices they are also non-negative;
- the eigenvectors can be chosen orthonormal;
- $C = V\Lambda V^\top$ (the **spectral decomposition**).

For a covariance matrix, the eigenvector with the largest eigenvalue is the direction in which the data
varies most, and that eigenvalue *is* the variance along it. This is exactly what PCA finds.

```python-run
import numpy as np
rng = np.random.RandomState(0)
# correlated 2-D data: stretched along the diagonal
X = rng.randn(500, 2) @ np.array([[3.0, 0.0], [0.0, 0.5]]) @ np.array([[0.8, 0.6], [-0.6, 0.8]])
Xc = X - X.mean(axis=0)
C = Xc.T @ Xc / (len(X) - 1)
vals, vecs = np.linalg.eigh(C)           # eigh: for symmetric matrices, ascending order
print("covariance:\n", C.round(2))
print("eigenvalues (variances along eigenvectors):", vals.round(2))
print("top direction:", vecs[:, -1].round(3))
```

## 6. The singular value decomposition (SVD)

Every matrix, square or not, has an SVD:

$$X = U\,S\,V^\top,\qquad U\in\mathbb{R}^{n\times r},\ S=\operatorname{diag}(s_1\ge s_2\ge\dots\ge 0),\ V\in\mathbb{R}^{p\times r}.$$

The columns of $U$ and of $V$ are orthonormal. You can read the SVD as three steps: rotate (with
$V^\top$), stretch along the axes (with $S$), then rotate again (with $U$). Three facts make it central to ML:

1. **PCA = SVD of the centred data.** $X_c^\top X_c = V S^2 V^\top$, so the right singular vectors are the
   covariance eigenvectors and $s_j^2/(n-1)$ are the variances. Computing PCA through the SVD avoids forming
   $X^\top X$, which squares the condition number.
2. **Best low-rank approximation** (the Eckart–Young theorem). Keeping the top $k$ singular triplets gives
   the rank-$k$ matrix closest to $X$. This underlies compression, latent semantic analysis and
   recommender-system matrix factorisation, and it is also the idea behind LoRA adapters.
3. **Stable least squares.** `np.linalg.lstsq` uses the SVD and handles rank-deficient $X$ gracefully.

```python-run
import numpy as np
rng = np.random.RandomState(0)
# a 50x40 matrix that is (almost) rank 3
A = rng.randn(50, 3) @ rng.randn(3, 40) + 0.01 * rng.randn(50, 40)
U, s, Vt = np.linalg.svd(A, full_matrices=False)
print("top singular values:", s[:6].round(2))
k = 3
A_k = U[:, :k] * s[:k] @ Vt[:k]
err = np.linalg.norm(A - A_k) / np.linalg.norm(A)
print(f"rank-{k} approximation relative error: {err:.4f}")
print("storage: full", A.size, "numbers vs rank-3", U[:, :k].size + k + Vt[:k].size)
```

> [!INTERVIEW]
> **"What is the relationship between PCA and SVD?"** Centre the data, $X_c = USV^\top$. The rows of $V^\top$
> are the principal axes, $US$ (equivalently $X_cV$) are the projected coordinates, and $s_j^2/(n-1)$ is the
> variance explained by component $j$. Follow-up: "Why centre?" Without centring, the first component points
> roughly at the data's mean instead of along its direction of greatest spread.

## 7. Dimensions and the curse of dimensionality

A few geometric facts explain why some algorithms struggle when there are many features:

- In high dimensions, random points are nearly **equidistant**. The ratio between the nearest and farthest
  neighbour distances tends to 1, so "nearest" neighbour carries less information. This is one reason
  Müller & Guido note that k-NN does badly with hundreds of features.
- Covering a space with samples needs exponentially many points as $p$ grows.
- Two random high-dimensional vectors are almost orthogonal, which is why random projections preserve
  distances surprisingly well.

```python-run
import numpy as np
rng = np.random.RandomState(0)
for p in [2, 10, 100, 1000]:
    X = rng.rand(200, p)
    d = np.linalg.norm(X[1:] - X[0], axis=1)
    print(f"p={p:5d}  min/max distance ratio = {d.min() / d.max():.3f}")
```

## 8. Cheat sheet

| Concept | numpy | Where it appears |
|---|---|---|
| dot product | `a @ b` | linear models, attention scores |
| matrix product | `A @ B` | layers, batch predictions |
| norm | `np.linalg.norm(x, ord)` | distances, regularisation |
| solve $Ax=b$ | `np.linalg.solve(A, b)` | normal equations |
| least squares | `np.linalg.lstsq(X, y)` | linear regression |
| eigendecomposition | `np.linalg.eigh(C)` | PCA via covariance, spectral clustering |
| SVD | `np.linalg.svd(X, full_matrices=False)` | PCA, low-rank models |
| transpose | `A.T` | gradients ($X^\top r$) |

## Summary

- Datasets are $n\times p$ matrices: rows are samples, columns are features.
- Dot products measure alignment, norms measure size, and distances are norms of differences.
- A matrix product applies a linear map to every row at once. Check shapes constantly.
- Least squares has the closed form $X^\top Xw = X^\top y$. Solve it rather than inverting.
- Eigenvectors of a covariance matrix are the directions of maximal variance, and the SVD computes them
  stably (PCA).
- High-dimensional geometry is counter-intuitive: distances concentrate.

```quiz
[
  {"q": "X has shape (100, 20) and W has shape (20, 5). What is the shape of X @ W?", "options": ["(100, 5)", "(20, 20)", "(5, 100)", "Error: shapes do not match"], "answer": 0,
   "explain": "Inner dimensions (20 and 20) match and disappear; the result has the outer dimensions (100, 5)."},
  {"q": "Two non-zero vectors have dot product 0. They are…", "options": ["orthogonal", "parallel", "identical", "both unit length"], "answer": 0,
   "explain": "a·b = |a||b|cosθ; with non-zero lengths, the product is 0 only when cosθ = 0, i.e. θ = 90°."},
  {"q": "Which penalty tends to drive some weights exactly to zero?", "options": ["L1 norm", "L2 norm squared", "L∞ norm", "None of them"], "answer": 0,
   "explain": "The L1 ball has corners on the axes, so the constrained optimum frequently lands where some coordinates are exactly zero (lasso)."},
  {"q": "Why prefer np.linalg.lstsq or solve over computing inv(X.T @ X) @ X.T @ y?", "options": ["They are faster and numerically more stable", "inv gives a different mathematical answer", "inv does not work on square matrices", "lstsq adds regularisation automatically"], "answer": 0,
   "explain": "Mathematically identical for full-rank X, but explicit inversion is slower and amplifies rounding errors, especially when X.T@X is ill-conditioned."},
  {"q": "For centred data X_c = U S V^T, the variance explained by component j is proportional to…", "options": ["s_j squared", "s_j", "the j-th column of U", "1/s_j"], "answer": 0,
   "explain": "X_c^T X_c = V S² V^T, so the covariance eigenvalues are s_j²/(n−1)."},
  {"q": "In numpy, for two 3×3 arrays A and B, A * B computes…", "options": ["the element-wise product", "the matrix product", "the dot product of flattened arrays", "the Kronecker product"], "answer": 0,
   "explain": "* is element-wise in numpy; use @ (or np.matmul) for matrix multiplication."},
  {"q": "As the number of features grows, the ratio min distance / max distance among random points…", "options": ["approaches 1", "approaches 0", "stays constant", "becomes negative"], "answer": 0,
   "explain": "Distances concentrate in high dimensions: all points look roughly equally far away, weakening nearest-neighbour methods."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 1 (NumPy, data as matrices) and ch. 3 (PCA); Goodfellow et al., *Deep Learning*, ch. 2 (background).
