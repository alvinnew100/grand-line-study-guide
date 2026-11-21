# Linear algebra for machine learning

> **Before this lesson:** basic Python only: variables, lists, `for` loops and calling a function. No earlier lesson is required; this is the first lesson of the track. School arithmetic (adding, multiplying, square roots) is all the maths assumed. Every symbol is explained when it first appears.

## In plain words

**Machine learning** (ML) is the craft of getting a computer to find patterns in examples instead of being told the rules by a programmer. The examples always arrive as numbers arranged in a grid, like a spreadsheet. **Linear algebra** is the branch of maths that deals with such grids and with lists of numbers: how to add them, multiply them, measure how big they are and how similar two of them are.

An everyday picture: a class register where each row is a pupil and each column is a test (maths, reading, science). One row is a list of that pupil's marks. Asking "which two pupils have the most similar marks?" or "what single number best sums up each pupil?" is linear algebra, even if nobody calls it that.

Why it matters for a job: almost every algorithm later in this track is a short recipe made of the operations in this lesson. Interviewers ask you to explain or code those recipes on a whiteboard, and at work the most common bug in ML code is a grid of the wrong size being fed into one of these operations. If you can picture the sizes, you can find the bug.

We use **NumPy**, the standard Python library for working with grids of numbers. It is imported with the line `import numpy as np`, which lets us write `np` as a short name for it.

## 1. Data as a matrix

Three words come first.

- A **scalar** is one number, such as `5.1`.
- A **vector** is an ordered list of numbers, such as `[5.1, 3.5, 1.4, 0.2]`. The order matters: the first number might be a length and the second a width.
- A **matrix** is a rectangular grid of numbers with rows and columns. Its **shape** is written "rows × columns", so a grid with 150 rows and 4 columns has shape 150 × 4.

Machine learning stores a dataset as one matrix, traditionally named $X$ (capital letters are used for matrices, lower-case letters for vectors and scalars).

- Each **row** is one **sample**: one thing we measured, such as one flower, one customer or one email. Samples are also called data points or instances.
- Each **column** is one **feature**: one kind of measurement taken on every sample, such as "petal length".
- The answer we want the computer to learn to predict for each sample is called its **label** (or **target**). The labels are kept in a separate vector named $y$, with one entry per row of $X$.

You will often see this written as $X \in \mathbb{R}^{n \times p}$. Read it as: "$X$ is a grid of ordinary decimal numbers with $n$ rows and $p$ columns". The symbol $\mathbb{R}$ stands for the real numbers (any number on the number line) and $\in$ means "belongs to". Likewise $y \in \mathbb{R}^n$ means "$y$ is a list of $n$ numbers". The book this track follows (Müller & Guido) and the scikit-learn library both use this layout, and so does this whole track.

The iris dataset, a classic collection of flower measurements, is a $150 \times 4$ matrix: 150 flowers, 4 measurements per flower.

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

**Reading this code line by line**

- `import numpy as np` loads NumPy. `from sklearn.datasets import load_iris` fetches one function from scikit-learn, the ML library used throughout the track. The first run takes a few seconds while the library loads.
- `iris = load_iris()` returns a bundle; `iris.data` is the matrix of measurements and `iris.target` is the vector of labels (0, 1 or 2 for the three species). `X, y = ...` gives them the usual names.
- `X.shape` is a pair `(rows, columns)`. It prints `(150, 4)`. `y.shape` prints `(150,)`: one number in the brackets means a plain list of 150 entries, not a grid.
- `X[0]` picks row 0. Python counts from 0, so this is the first flower: `[5.1 3.5 1.4 0.2]`.
- `X[:5, 0]` uses two positions separated by a comma: rows first, then columns. `:5` means "rows 0 to 4" and `0` means "column 0", so it prints the first feature of the first five flowers.

> [!TIP]
> When code misbehaves, print `.shape` first. Most ML bugs come from shapes: a missing axis, rows and columns swapped, or two arrays combined in a way you did not intend.

## 2. Vectors, the dot product and norms

A vector can be pictured in two ways: as a point (the vector `[3, 4]` is the point 3 steps right and 4 steps up) or as an arrow from the starting point `[0, 0]`, called the **origin**, to that point. With more than three numbers we cannot draw it, but the arithmetic is the same. The count of numbers in a vector is its **dimension**.

### The dot product

The **dot product** takes two vectors of the same length and returns one number: multiply the entries in matching positions, then add up the results. For $a = [3, 4]$ and $c = [6, 8]$ it is $3\times6 + 4\times8 = 18 + 32 = 50$.

In symbols:

$$a \cdot b = a^\top b = \sum_{j=1}^p a_j b_j = \lVert a\rVert\,\lVert b\rVert\cos\theta .$$

Reading the notation: $a_j$ is the $j$-th entry of $a$. The large $\sum$ (the Greek letter sigma) means "add up": here, add $a_j b_j$ for $j = 1, 2, \dots, p$. The form $a^\top b$ is another way of writing the same thing (the small $\top$, "transpose", is explained in section 3). The last form says the dot product also equals the length of $a$ times the length of $b$ times the cosine of the angle $\theta$ between the two arrows. You do not need trigonometry to use it. What it tells you is the sign:

- **positive** when the arrows point in a similar direction,
- **zero** when they are at a right angle; such vectors are called **orthogonal** (perpendicular),
- **negative** when they point in opposite directions.

So the dot product measures how much two vectors agree. It appears everywhere. A **linear model** (lesson 21) predicts with $\hat y = w^\top x + b$: multiply each feature in $x$ by its own **weight** in $w$ (a number saying how much that feature counts), add them up, then add a constant $b$. The hat on $\hat y$ ("y-hat") marks a prediction, as opposed to the true label $y$.

### Norms: how long is a vector?

A **norm** is a rule that turns a vector into one non-negative number measuring its size. Three are common.

| norm | in words | formula | ML use |
|---|---|---|---|
| L2 (Euclidean) | straight-line length: square every entry, add, take the square root | $\lVert x\rVert_2 = \sqrt{\sum_j x_j^2}$ | distances in k-NN and k-means, ridge penalty |
| L1 (Manhattan) | add up the sizes of the entries, ignoring signs | $\lVert x\rVert_1 = \sum_j \lvert x_j\rvert$ | lasso penalty (pushes weights to exactly zero), mean absolute error |
| L∞ (max) | the size of the biggest entry | $\max_j \lvert x_j\rvert$ | bounds on how far an input may be nudged |

The double bars $\lVert x \rVert$ mean "norm of $x$" and the single bars $\lvert x_j \rvert$ mean absolute value (drop the minus sign). Worked example for $a = [3, 4]$: L2 is $\sqrt{9 + 16} = \sqrt{25} = 5$ (the 3-4-5 triangle), L1 is $3 + 4 = 7$ (walking along city blocks instead of cutting the corner, hence "Manhattan"), L∞ is $4$.

Two measures of likeness are built from these:

- The **Euclidean distance** between two samples is the L2 norm of their difference, $\lVert a - b\rVert_2$. Subtract entry by entry, then measure the length. For $a = [3,4]$ and $c = [6,8]$ the difference is $[-3,-4]$, with length 5.
- The **cosine similarity** is the dot product divided by both lengths, $\frac{a\cdot b}{\lVert a\rVert\lVert b\rVert}$. It is 1 for the same direction, 0 for a right angle and −1 for opposite directions. Because dividing by the lengths removes them, it compares direction only. For $a$ and $c$: $50 / (5 \times 10) = 1$; $c$ is $a$ doubled, so they point the same way. This is the standard similarity for text, where a long document and a short one about the same subject should count as alike.

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

**Reading this code line by line**

- `np.array([3.0, 4.0])` turns a Python list into a NumPy **array**, NumPy's container for vectors and matrices. Arithmetic on arrays works on all entries at once.
- `a @ b` is the dot product. `@` is Python's operator for it. Here $3\times4 + 4\times(-3) = 0$, so `a` and `b` are orthogonal.
- `np.linalg.norm(a)` is the L2 norm (5.0). A second argument of `1` asks for the L1 norm (7.0). `linalg` is NumPy's linear-algebra toolbox.
- `a - c` subtracts entry by entry; its norm is the distance, 5.0.
- The last two lines compute the cosine similarity by hand: 1.0.

A useful identity for vectors of length 1 (called **unit vectors**): $\lVert a-b\rVert^2 = 2 - 2\cos\theta$. Dividing a vector by its own L2 norm, called **L2-normalising**, makes it a unit vector. After doing that to every vector, sorting by smallest distance and sorting by largest cosine similarity give the same order. Vector databases, which power search over text and images, rely on this.

## 3. Matrices as machines that transform vectors

A matrix is more than a table for storing data. Multiplying a vector by a matrix produces a new vector, so a matrix also acts as a machine: vectors in, vectors out. This kind of transformation is called a **linear map**.

First, the **transpose**. Written $A^\top$ (code: `A.T`), it flips a matrix so that rows become columns. A 2 × 3 matrix becomes a 3 × 2 one. For a vector it marks the difference between a list written across (a row) and a list written downwards (a column), which is why the dot product is written $a^\top b$: a row times a column.

**Matrix multiplication** is built from dot products. To compute $C = AB$, take each row of $A$ and each column of $B$ and take their dot product; that number goes in the matching row and column of $C$.

$$\underbrace{A}_{n\times p}\ \underbrace{B}_{p\times q} = \underbrace{C}_{n\times q},\qquad C_{ik} = \sum_j A_{ij}B_{jk}.$$

$C_{ik}$ means "the entry in row $i$, column $k$". The rule to remember: the **inner sizes must match** (the $p$ and $p$ above), and they disappear; the outer sizes ($n$ and $q$) give the shape of the answer. A tiny example:

$$\begin{bmatrix}1 & 2\\ 3 & 4\end{bmatrix}\begin{bmatrix}5\\ 6\end{bmatrix} = \begin{bmatrix}1\times5 + 2\times6\\ 3\times5 + 4\times6\end{bmatrix} = \begin{bmatrix}17\\ 39\end{bmatrix}.$$

A 2 × 2 times a 2 × 1 gives a 2 × 1.

Why this matters: applying a model to a whole dataset is one matrix product. For a linear model, $\hat y = Xw + b$ gives all $n$ predictions at once, because each row of $X$ is dotted with $w$. A layer of a **neural network** (lesson 23) computes $H = XW + b$: it turns $n$ samples with $p$ features into $n$ samples with $q$ new numbers each, where $W$ is a $p \times q$ matrix of weights.

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

**Reading this code line by line**

- `np.random.RandomState(0)` creates a random-number generator. The `0` is a **seed**: with the same seed you get the same "random" numbers on every run, so results can be repeated.
- `rng.randn(5, 3)` makes a 5 × 3 matrix of random numbers centred on zero.
- `X @ W` is the matrix product: (5, 3) times (3, 2) gives (5, 2). Between two matrices `@` means matrix multiplication; between two vectors it is the dot product.
- `+ b` adds a 2-entry vector to a 5 × 2 matrix. NumPy repeats `b` on every row. This automatic stretching is called **broadcasting**.
- `np.allclose(...)` checks that two arrays are equal up to tiny rounding error. It prints `True`: row 0 of the result is row 0 of `X` pushed through the same machine.

Facts you will use constantly:

- $(AB)^\top = B^\top A^\top$: transposing a product reverses the order.
- You may regroup a chain of products, $(AB)C = A(BC)$, but you may **not** swap the order: in general $AB \ne BA$.
- The **identity matrix** $I$ has 1s on the diagonal and 0s elsewhere, and plays the part of the number 1: $AI = A$. An **inverse** $A^{-1}$ undoes $A$: $AA^{-1} = I$. Only square matrices (same number of rows and columns) can have one, and not all do. In practice you almost never compute an inverse. To find the $x$ that satisfies $Ax = b$, call `np.linalg.solve` or `np.linalg.lstsq`, which are faster and lose less precision.
- **Broadcasting**: NumPy stretches an array of size 1 along an axis to match the other array. `X - X.mean(axis=0)` subtracts each column's average from that column (`axis=0` means "go down the rows", giving one average per column). This is called **centring** the data.

> [!WARNING]
> `A * B` in NumPy multiplies **entry by entry** (the Hadamard product, written $A\odot B$). For a matrix product use `A @ B`. Mixing them up is a classic silent bug: when both matrices are square, both operations run without an error and give different answers.

## 4. Rank, linear independence and least squares

Suppose a dataset holds temperature in °C in one column and the same temperature in °F in another. The second column adds no information, because it can be computed from the first. Linear algebra has names for this.

- The columns of $X$ are **linearly independent** if no column can be written as a weighted sum of the others.
- The **rank** of $X$ is the number of independent columns: how much distinct information the matrix holds.
- Features that can be computed (exactly or nearly) from each other are called **collinear**.

When features are collinear, rank drops, and a linear model has infinitely many equally good sets of weights: it could put all the weight on °C, all on °F, or split it any way. The weights the computer returns then swing wildly with tiny changes in the data. Ridge regression (lesson 21) repairs this by adding a small number $\alpha$ to the diagonal of the system (adding $\alpha I$), which guarantees a single answer.

### Least squares

Fitting a line to data means choosing weights $w$ so that the predictions $Xw$ are as close as possible to the labels $y$. The gap for each sample, $y_i - \hat y_i$, is its **residual**. **Ordinary least squares** (OLS) picks the $w$ that makes the sum of squared residuals, written $\lVert y - Xw\rVert^2$, as small as possible. Squaring makes every gap positive and punishes big gaps more.

The next lesson shows that the best $w$ satisfies the **normal equations**:

$$X^\top X\,w = X^\top y .$$

In words: a set of $p$ ordinary equations in the $p$ unknown weights, which a computer solves directly. The picture behind it: all the predictions that $X$ can possibly produce (every weighted sum of its columns, called the **column space**) form a flat surface, and the best prediction is the point on that surface nearest to $y$. At that point the residual sticks straight out of the surface, orthogonal to every column. "Normal" is an old word for perpendicular.

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

What the lines do: `np.ones((20, 1))` is a column of twenty 1s, and `np.hstack` glues it to the left of two random feature columns. A column of 1s lets the first weight act as the constant term (the **intercept**). The labels are made from known weights `[0.5, 2.0, -1.0]` plus a little random noise, so we know what the right answer is. `np.linalg.solve(A, b)` solves $Ax = b$; here it solves the normal equations. `np.linalg.lstsq` does least squares directly and returns several things, of which `[0]` is the weights. Both print values close to the true weights, and the last line shows the residual's dot product with every column is zero, as the picture promised.

## 5. Eigenvectors: directions a matrix only stretches

Most vectors change direction when multiplied by a matrix. For a square matrix $A$, a few special directions do not: the vector comes out pointing the same way, only longer or shorter. Such a vector $v$ (not all zeros) is an **eigenvector**, and the stretch factor $\lambda$ (the Greek letter lambda) is its **eigenvalue**:

$$Av = \lambda v .$$

Tiny example: with $A = \begin{bmatrix}2 & 0\\ 0 & 3\end{bmatrix}$, the vector $[1, 0]$ comes out as $[2, 0]$, the same direction doubled, so it is an eigenvector with eigenvalue 2. Likewise $[0, 1]$ has eigenvalue 3.

The matrix that matters most here is the **covariance matrix**. The **variance** of a feature is a number saying how spread out its values are (the average squared distance from the mean). The **covariance** of two features says whether they rise and fall together. Put all of these in a $p \times p$ grid and you have the covariance matrix, computed from centred data $X_c$ as $C = \frac{1}{n-1}X_c^\top X_c$. It is **symmetric** (equal to its own transpose), and symmetric matrices behave well:

- all eigenvalues are real numbers, and for a covariance matrix they are never negative;
- the eigenvectors can be chosen **orthonormal**: each of length 1 and all at right angles to one another;
- the matrix can be rebuilt from them, $C = V\Lambda V^\top$, where the columns of $V$ are the eigenvectors and $\Lambda$ (capital lambda) is a matrix with the eigenvalues on its diagonal. This is the **spectral decomposition**.

The pay-off: for a covariance matrix, the eigenvector with the largest eigenvalue is the direction along which the data is most spread out, and the eigenvalue *is* the variance in that direction. Finding these directions is what principal component analysis (PCA, lesson 31) does.

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

The long line builds a cloud of 500 points, stretches it (3 times along one axis, 0.5 along the other) and rotates it. The next two lines centre the data and compute the covariance matrix from the formula above. `np.linalg.eigh` returns the eigenvalues, smallest first, and a matrix whose columns are the eigenvectors; `vecs[:, -1]` is the last column, the direction of greatest spread. The eigenvalues come out near 0.25 and 9, the squares of the stretch factors 0.5 and 3, and the top direction is close to `[0.8, 0.6]` (possibly with both signs flipped, which is the same line).

## 6. The singular value decomposition (SVD)

Eigenvectors need a square matrix, but a data matrix is rarely square. The **singular value decomposition** works for any matrix. It splits $X$ into three simpler matrices that multiply back to $X$:

$$X = U\,S\,V^\top,\qquad U\in\mathbb{R}^{n\times r},\ S=\operatorname{diag}(s_1\ge s_2\ge\dots\ge 0),\ V\in\mathbb{R}^{p\times r}.$$

$S$ is zero everywhere except its diagonal, which holds the **singular values** $s_1, s_2, \dots$, sorted from largest to smallest and never negative. The columns of $U$ and of $V$ are orthonormal. One way to read it: any matrix does three things in turn, a rotation ($V^\top$), a stretch along the axes ($S$), and another rotation ($U$). The singular values say how much stretching happens in each direction; a big one marks an important direction, a tiny one a direction that hardly matters.

Three facts make the SVD central to ML:

1. **PCA is the SVD of the centred data.** Since $X_c^\top X_c = V S^2 V^\top$, the columns of $V$ are the eigenvectors of the covariance matrix, and $s_j^2/(n-1)$ are the variances. Going through the SVD avoids forming $X^\top X$ at all, which matters because that product magnifies rounding errors.
2. **Best low-rank approximation** (the Eckart–Young theorem). Keep only the $k$ largest singular values and their columns of $U$ and $V$, and you get the rank-$k$ matrix closest to $X$. This is the idea behind compression, latent semantic analysis for text, matrix factorisation in recommender systems, and LoRA adapters for large language models.
3. **Stable least squares.** `np.linalg.lstsq` uses the SVD and copes when $X$ has collinear columns.

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

The matrix `A` is a 50 × 3 times a 3 × 40, so it holds only three independent directions, plus a whisper of noise. `np.linalg.svd` returns $U$, the singular values as a vector `s`, and $V^\top$ as `Vt`. The output shows three large singular values, then a sharp drop to near zero: the SVD has discovered that only three directions matter. Rebuilding from those three (`A_k`) gives an error well under 1%, while storing 273 numbers instead of 2,000.

> [!INTERVIEW]
> **"What is the relationship between PCA and SVD?"** Centre the data, then $X_c = USV^\top$. The rows of $V^\top$ are the principal axes, $US$ (the same as $X_cV$) holds each sample's new coordinates, and $s_j^2/(n-1)$ is the variance explained by component $j$. Follow-up: "Why centre?" Without centring, the first component points roughly from the origin towards the data's average instead of along its direction of greatest spread.

## 7. Dimensions and the curse of dimensionality

Each feature is one dimension, so a dataset with 1,000 features lives in 1,000-dimensional space. Our intuition, trained on two and three dimensions, fails there. The trouble this causes is nicknamed the **curse of dimensionality**.

- In high dimensions, random points are nearly **the same distance apart**. The nearest neighbour and the farthest neighbour are almost equally far, so "nearest" says little. This is one reason the k-nearest-neighbours method (lesson 20) does poorly with hundreds of features.
- Filling a space with samples needs exponentially more points as $p$ grows. Ten points cover a line reasonably; covering a 10-dimensional cube as densely takes $10^{10}$.
- Two random high-dimensional vectors are almost orthogonal. That has an upside: projecting data onto a few random directions preserves distances surprisingly well.

```python-run
import numpy as np
rng = np.random.RandomState(0)
for p in [2, 10, 100, 1000]:
    X = rng.rand(200, p)
    d = np.linalg.norm(X[1:] - X[0], axis=1)
    print(f"p={p:5d}  min/max distance ratio = {d.min() / d.max():.3f}")
```

For each number of features `p`, the loop draws 200 random points, measures the distance from the first point to all the others (`axis=1` takes the norm of each row) and divides the smallest distance by the largest. With 2 features the ratio is close to 0: some points are very near and some far. With 1,000 features it climbs towards 1: everything is about equally far away.

## 8. Cheat sheet

| Concept | NumPy | Where it appears |
|---|---|---|
| dot product | `a @ b` | linear models, attention scores |
| matrix product | `A @ B` | layers, predictions for many rows |
| norm | `np.linalg.norm(x, ord)` | distances, regularisation |
| solve $Ax=b$ | `np.linalg.solve(A, b)` | normal equations |
| least squares | `np.linalg.lstsq(X, y)` | linear regression |
| eigendecomposition | `np.linalg.eigh(C)` | PCA via covariance, spectral clustering |
| SVD | `np.linalg.svd(X, full_matrices=False)` | PCA, low-rank models |
| transpose | `A.T` | gradients ($X^\top r$) |

## Summary

- Datasets are $n\times p$ matrices: rows are samples, columns are features, labels sit in a separate vector.
- Dot products measure agreement, norms measure size, and distances are norms of differences.
- A matrix product applies the same transformation to every row at once. Check shapes constantly.
- Least squares has the closed form $X^\top Xw = X^\top y$. Solve it; do not invert.
- Eigenvectors of a covariance matrix are the directions of greatest spread, and the SVD computes them reliably (PCA).
- High-dimensional geometry is counter-intuitive: distances bunch together.

## Glossary

- **Scalar / vector / matrix**: one number / an ordered list of numbers / a rectangular grid of numbers.
- **Shape**: the size of an array, written rows × columns.
- **Sample, feature, label**: one row of the data / one column of the data / the answer to be predicted for a row.
- **Dot product**: multiply matching entries of two vectors and add the results; measures agreement.
- **Orthogonal**: at a right angle; dot product zero.
- **Norm**: a measure of a vector's size (L2 is straight-line length, L1 is the sum of absolute values).
- **Cosine similarity**: the dot product divided by both lengths; compares direction only.
- **Transpose**: a matrix with rows and columns swapped.
- **Broadcasting**: NumPy's automatic stretching of a smaller array to fit a larger one.
- **Rank**: the number of columns that carry independent information.
- **Collinear**: features that can be computed from one another.
- **Residual**: true value minus predicted value.
- **Least squares**: choosing weights that minimise the sum of squared residuals.
- **Eigenvector / eigenvalue**: a direction a matrix only stretches / the stretch factor.
- **Covariance matrix**: a grid recording how spread out each feature is and how pairs of features move together.
- **Singular value decomposition (SVD)**: splitting any matrix into rotation, stretch, rotation.
- **Curse of dimensionality**: the problems that appear when data has very many features.

## Check yourself

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
