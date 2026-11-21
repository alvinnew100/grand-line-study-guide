# Dimensionality reduction: PCA, NMF and t-SNE

> **Before this lesson:** you need scaling and the `fit`/`transform` pattern from [Preprocessing and scaling](#/lesson/ml/preprocessing-scaling). The maths sections use variance, the covariance matrix, eigenvectors and the singular value decomposition from [Linear algebra for ML](#/lesson/ml/linear-algebra) (sections 5 and 6); each is recalled in a sentence where it appears.

## In plain words

The number of features a dataset has is called its **dimensionality**: a table with 30 columns is 30-dimensional. **Dimensionality reduction** means describing each sample with fewer numbers while losing as little information as possible.

Think of photographing a sculpture. The sculpture is three-dimensional and the photo is flat, so something is lost, but the angle matters enormously. A shot from the front shows the shape; a shot from directly above shows a blob. Dimensionality reduction is the search for the most revealing angle.

There are three reasons to do it: **visualisation** (people can look at two dimensions, not thirty), **compression** (less memory, faster models) and finding a description of the data that is **more useful** to a later model than the raw features. This lesson covers three methods: principal component analysis (the workhorse), non-negative matrix factorisation (which finds additive "parts") and t-SNE (for two-dimensional pictures).

Why this matters for a job: PCA is everywhere, in exploratory analysis, in preprocessing, and in interview questions ("explain PCA", "how do PCA and SVD relate?", "why can't you trust distances in a t-SNE plot?").

## 1. Principal component analysis (PCA)

Suppose a cloud of data points has the shape of a cigar lying diagonally. Describing each point by its horizontal and vertical position is wasteful: the two numbers rise and fall together, so each partly repeats the other. It would be better to describe each point by "how far along the cigar" and "how far off its centre line". The first number alone captures most of what distinguishes one point from another.

**Principal component analysis** finds those new axes automatically. It **rotates** the coordinate system to line up with the directions in which the data is most spread out. The algorithm in words:

1. Find the direction along which the data has the largest **variance** (spread). A direction with a lot of spread carries a lot of information about how samples differ. This is *component 1*.
2. Among all directions at right angles (**orthogonal**) to the first, find the one with the largest variance. This is *component 2*.
3. Continue until there are as many components as original features.

These directions are the **principal components**. To transform the data, subtract each feature's mean (so the cloud is centred on zero) and express every point in the new axes. Two things are true of the result. The new features are **uncorrelated**: none can be predicted from another by a straight-line rule. And they are sorted by importance, so to reduce the dimensionality you keep the first $k$ and drop the rest.

### The maths

Let $X_c$ be the data matrix with each column's mean subtracted (the **centred** data), with $n$ rows and $p$ columns. The singular value decomposition (SVD) splits it into three matrices, $X_c = USV^\top$, where $S$ holds the singular values $s_1 \ge s_2 \ge \dots$ on its diagonal. Everything PCA produces can be read off:

- the principal directions are the rows of $V^\top$. scikit-learn stores them in `pca.components_`, with shape `(k, p)`: one row per component, one column per original feature;
- the new coordinates of the samples are $Z = X_cV_k = U_kS_k$, where the subscript $k$ means "keep the first $k$ columns". This is what `pca.transform(X)` returns;
- the variance along component $j$ is $s_j^2/(n-1)$ (`explained_variance_`). Its share of the total, $s_j^2/\sum_i s_i^2$, is the **explained variance ratio** (`explained_variance_ratio_`): the fraction of the data's total spread that this one component accounts for;
- going back is $\hat X = ZV_k^\top + \bar x$ (`inverse_transform`): rotate back and add the mean $\bar x$. If components were dropped, $\hat X$ is an approximation of the original data, called the **reconstruction**. Of all the ways to describe the data with $k$ numbers per sample using straight-line combinations of the features, PCA's has the smallest squared reconstruction error.

```python-run
import numpy as np
from sklearn.decomposition import PCA
rng = np.random.RandomState(5)
X = rng.randn(300, 2) @ np.array([[2.0, 0.0], [0.0, 0.4]]) @ np.array([[0.8, 0.6], [-0.6, 0.8]]) + [5, -3]

pca = PCA(n_components=2).fit(X)
print("mean_:", pca.mean_.round(2))
print("components_ (rows are directions):\n", pca.components_.round(3))
print("explained_variance_ratio_:", pca.explained_variance_ratio_.round(3))

# the same thing by hand with the SVD
Xc = X - X.mean(axis=0)
U, S, Vt = np.linalg.svd(Xc, full_matrices=False)
print("SVD directions (signs may differ):\n", Vt.round(3))
print("ratio from S^2:", (S ** 2 / (S ** 2).sum()).round(3))
Z = pca.transform(X)
print("covariance of transformed data (off-diagonals ~ 0):\n", np.cov(Z.T).round(3))
```

**Reading this code line by line**

- The long line builds the diagonal cigar: 300 random points, stretched (by 2 along one axis and 0.4 along the other), rotated so the long axis points along the direction (0.8, 0.6), and moved so the centre is at (5, −3).
- `PCA(n_components=2).fit(X)` learns the mean and the two components. `pca.mean_` prints about (5, −3), the centre we chose.
- `pca.components_` prints the two directions as rows. The first is about (0.80, 0.60): PCA has recovered the cigar's long axis without being told it.
- `explained_variance_ratio_` is (0.962, 0.038): 96% of the spread lies along the first component.
- The next block repeats the calculation by hand: centre, take the SVD, read the directions from `Vt` and the ratios from the squared singular values. The numbers match, except that the signs of a direction may be flipped (section 5 explains why that is harmless).
- The last lines transform the data and print its covariance matrix (`np.cov`). The entries off the diagonal are 0: the new features are uncorrelated.

### PCA for visualisation

The tumour dataset has 30 features. Looking at them two at a time would take 435 charts. PCA gives one two-dimensional view that captures the main variation. **Scale the features first**: PCA looks for the largest variance, and a feature recorded in large units would win for that reason alone.

```python-run
import numpy as np
from sklearn.datasets import load_breast_cancer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

cancer = load_breast_cancer()
X_scaled = StandardScaler().fit_transform(cancer.data)
pca = PCA(n_components=2).fit(X_scaled)
Z = pca.transform(X_scaled)
print("original shape:", X_scaled.shape, "-> reduced shape:", Z.shape)
print("variance explained by 2 components:", pca.explained_variance_ratio_.sum().round(3))
for c in (0, 1):
    print(f"class {cancer.target_names[c]:9s} mean on PC1 = {Z[cancer.target == c, 0].mean():6.2f}")
top = np.argsort(np.abs(pca.components_[0]))[::-1][:4]
print("largest loadings on PC1:", [str(cancer.feature_names[i]) for i in top])
```

After standardising, PCA reduces the table from 30 columns to 2, and those two components hold 63% of the total variance. `Z[cancer.target == c, 0]` selects the first component's values for the tumours of one class; the malignant tumours average 3.71 on it and the benign ones −2.21. PCA never saw the labels, yet the two classes fall on opposite sides of the first component. A chart of the two components would show two fairly distinct clouds.

The drawback is that **the new axes are hard to interpret**. Each component is a weighted mix of all 30 original features. The weights, the entries of `components_`, are called **loadings**. The last two lines list the four features with the largest loadings on the first component, which gives a hint of what it measures (here, how indented the tumour's outline is), but "0.26 times this plus 0.26 times that, and so on for 30 terms" is not a quantity a doctor can reason about.

### How many components?

Add up the explained variance ratios in order to get the **cumulative explained variance**, and keep enough components to reach a target such as 95%. scikit-learn will do it for you: `PCA(n_components=0.95)` keeps as many components as are needed to explain 95% of the variance.

```python-run
import numpy as np
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
X = load_digits().data                       # 1797 images of 8x8 = 64 pixels
pca = PCA().fit(X)
cum = np.cumsum(pca.explained_variance_ratio_)
for k in [2, 5, 10, 20, 40]:
    print(f"{k:2d} components explain {cum[k - 1]:.1%} of the variance")
print("components needed for 95%:", PCA(n_components=0.95).fit(X).n_components_)
```

`load_digits` is a set of 1,797 small images of handwritten digits. Each image is 8 × 8 pixels, flattened into a row of 64 brightness values. `PCA()` with no argument keeps every component, and `np.cumsum` gives the running total of the ratios. Two components hold 28.5% of the variance, ten hold 73.8%, and 29 are enough for 95%: more than half the columns can be dropped at the cost of 5% of the variance.

### PCA for feature extraction: eigenfaces

A classic use of PCA is on photographs of faces. Raw pixels are a poor way to compare two pictures: shift a face one pixel sideways and almost every pixel value changes, though it is the same face. With PCA, each face is rewritten as a weighted sum of a hundred or so component images, nicknamed **eigenfaces**, which capture broad patterns such as the direction of the lighting or the contrast between face and background. Distances between those weights are more meaningful than distances between pixels, and a nearest-neighbour classifier on the faces becomes noticeably more accurate (in the source book's experiment on 62 people, about 31% correct instead of about 23%).

The option `whiten=True` adds one step: after the rotation, each component is rescaled to variance 1, as if `StandardScaler` were applied to the new features. That stops the first few components from dominating distances.

The face images need a download, so the demonstration below uses the digit images. They are already centred and aligned, so raw pixels work well and PCA does not raise the accuracy. What it shows instead is **compression**.

```python-run
import numpy as np
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import train_test_split

X, y = load_digits(return_X_y=True)
X_tr, X_te, y_tr, y_te = train_test_split(X, y, random_state=0)
print(f"1-NN on 64 raw pixels: {KNeighborsClassifier(1).fit(X_tr, y_tr).score(X_te, y_te):.3f}")
for k in [2, 8, 16, 32]:
    pca = PCA(n_components=k, whiten=True, random_state=0).fit(X_tr)        # fit on the training set only
    acc = KNeighborsClassifier(1).fit(pca.transform(X_tr), y_tr).score(pca.transform(X_te), y_te)
    rec = pca.inverse_transform(pca.transform(X_te))
    print(f"k={k:2d}: 1-NN accuracy={acc:.3f}  reconstruction MSE={np.mean((X_te - rec) ** 2):.2f}")
```

A 1-nearest-neighbour classifier on all 64 pixels scores 0.991. The loop then fits PCA on the training images only (the same rule as for scalers), transforms both sets, and classifies using only $k$ numbers per image. With 2 components the accuracy is 0.538; with 16 it is 0.982. Sixteen numbers per image, a quarter of the original, keep nearly all of the accuracy. The last column is the **reconstruction error**: transform the test images, transform them back with `inverse_transform`, and measure the mean squared difference from the originals. It falls steadily as components are added.

> [!INTERVIEW]
> **"Explain PCA and its limits."** It is a linear, unsupervised method that finds orthogonal directions of maximum variance: the eigenvectors of the covariance matrix, computed in practice by an SVD of the centred data. It is used for compression, for removing correlation between features, for reducing noise and for visualisation. Limits: it can only rotate, so it misses curved structure; it is sensitive to scaling and to outliers; the directions of greatest variance are not necessarily the most *predictive* ones, because it ignores the labels; and the components are hard to interpret.

## 2. Non-negative matrix factorisation (NMF)

Like PCA, **non-negative matrix factorisation** writes each sample as a weighted sum of a few components. In matrix form the data $X$ is approximated by a product $X \approx WH$, where one matrix holds the components and the other holds each sample's weights. The difference is one rule: **every component and every weight must be zero or positive**. NMF therefore applies only to data in which no feature is negative, such as pixel brightness, word counts, or the loudness of each pitch in a sound recording.

Why the rule helps: with no negative weights, components cannot cancel one another out. Each one can only *add* something. The result is a description in terms of **parts**, which people often find much easier to interpret than PCA's components. This suits data that really is a sum of separate sources, such as a recording of several people talking at once, or music with several instruments. On images of faces, NMF's components look like recognisable pieces and typical poses, where PCA's look like ghostly overall patterns of light and dark.

Other differences from PCA:

- The components have no order. None is "first"; all play an equal part.
- **Changing the number of components changes all of them.** With PCA, the first 15 components are the same whether you ask for 15 or 20. With NMF they are not.
- NMF starts from random numbers and improves them step by step, so the result can depend on the random seed.
- It is used mostly for discovering patterns, and less for compressing data.

```python-run
import numpy as np
from sklearn.decomposition import NMF, PCA

# three non-negative "sources" mixed with non-negative weights, as in the book's signal example
t = np.linspace(0, 8, 400)
S = np.column_stack([np.abs(np.sin(2 * t)), (t % 2) / 2, (np.sin(5 * t) > 0).astype(float)])
rng = np.random.RandomState(0)
A = rng.uniform(0.2, 1.0, size=(20, 3))            # 20 measurement devices
X = S @ A.T                                        # each row: 20 mixed measurements

H_nmf = NMF(n_components=3, init="nndsvd", max_iter=2000, random_state=0).fit_transform(X)
H_pca = PCA(n_components=3).fit_transform(X)
def best_match(H):
    c = np.abs(np.corrcoef(S.T, H.T)[:3, 3:])
    return c.max(axis=1).round(2)
print("correlation of each true source with its best NMF component:", best_match(H_nmf))
print("correlation of each true source with its best PCA component:", best_match(H_pca))
print("NMF outputs all non-negative:", (H_nmf >= 0).all(), "| PCA outputs non-negative:", (H_pca >= 0).all())
```

**Reading this code line by line**

- `S` holds three hidden signals over 400 time steps: a series of humps, a sawtooth and an on/off square wave. None is ever negative. These are the "sources" we pretend not to know.
- `A` is a 20 × 3 table of random positive mixing weights, and `X = S @ A.T` is what 20 measuring devices would record: each records a different positive blend of the three sources. The task is to recover the sources from `X` alone.
- `NMF(...).fit_transform(X)` and `PCA(...).fit_transform(X)` each produce three components per time step.
- `best_match` computes the correlation between every true source and every recovered component (`np.corrcoef`), and reports, for each source, the strongest match. A value of 1.00 means a perfect recovery.

NMF recovers the sources almost exactly (correlations of 1.00, 0.95 and 0.97). PCA's components match them less well (0.83, 0.71, 0.77), because PCA's goal is to capture variance, and it is free to blend the sources and to use negative values to do so.

Related methods you may see named: independent component analysis (ICA), factor analysis (FA) and sparse coding, also called dictionary learning.

## 3. Manifold learning with t-SNE

PCA is a good first look at a dataset, but a rotation is a limited tool. If the samples lie on a curved surface inside the high-dimensional space (such a surface is called a **manifold**), no rotation can flatten it. **Manifold learning** methods allow much more flexible mappings and often give far better pictures. The best known is **t-SNE** (t-distributed stochastic neighbour embedding). The output of such a method, a position in two dimensions for every sample, is called an **embedding**.

How it works: t-SNE places every sample at a random position on a flat page, then repeatedly nudges the positions so that samples which were **close neighbours in the original space end up close on the page**. It cares much more about keeping neighbours together than about getting large distances right. Technically, it converts distances into probabilities of "being neighbours", once in the original space and once on the page, and adjusts the positions to make the two sets of probabilities agree, measured by the KL divergence (a measure of the gap between two probability distributions, from the probability lesson). On the page it uses a distribution with heavy tails, the Student t-distribution that gives the method its name, which leaves room for separate groups to spread apart.

Properties to remember:

- It has only `fit_transform`. There is **no `transform` for new data**: you cannot place a fresh sample into an existing picture. It is a tool for exploring a dataset, not a preprocessing step for a model.
- It uses no labels, yet on the handwritten digits it separates the ten digits far more cleanly than the first two principal components.
- Its main setting is `perplexity`, roughly the number of neighbours each point pays attention to (values from 5 to 50 are typical). The default usually works.
- **Reading a t-SNE picture**: the *sizes* of the groups and the *distances between groups* mean very little, and a different random seed gives a different layout. Only which points are neighbours can be trusted.
- It is slow on large datasets. A common trick is to reduce to about 50 dimensions with PCA first. **UMAP** is a popular, faster alternative with similar aims.

```python-run
import numpy as np
from sklearn.datasets import load_digits
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE
from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_score

X, y = load_digits(return_X_y=True)
X, y = X[:300], y[:300]                       # small subset keeps this fast in the browser
Z_pca = PCA(n_components=2).fit_transform(X)
Z_tsne = TSNE(n_components=2, random_state=42, init="pca").fit_transform(X)
# how well separated are the digit classes in each 2-D picture? (5-NN accuracy within the embedding)
for name, Z in [("PCA  ", Z_pca), ("t-SNE", Z_tsne)]:
    acc = cross_val_score(KNeighborsClassifier(5), Z, y, cv=5).mean()
    print(f"{name} 2-D embedding: neighbours share a digit label {acc:.1%} of the time")
```

Both methods reduce 300 digit images from 64 dimensions to 2. Since charts are not available here, the quality of each picture is measured instead: a 5-nearest-neighbour classifier is run *inside* the two-dimensional picture, which asks how often a point's neighbours on the page show the same digit. In the PCA picture that happens 70% of the time; in the t-SNE picture, 97%. The labels are used only for this check, not by either method. This demo takes a few seconds, because t-SNE is the slowest method in the lesson.

## 4. Choosing a method

| goal | method |
|---|---|
| compress features, or remove correlation between them, before a model | PCA, fitted on the training data, inside a pipeline |
| a quick two-dimensional look at the data | PCA |
| interpretable additive parts from non-negative data | NMF |
| the clearest two-dimensional picture of groups in the data | t-SNE or UMAP, for exploration only |
| sparse data with very many features, such as word counts | `TruncatedSVD`, which is PCA without the centring step and so keeps the data sparse |

## 5. Worked example: PCA on four points by hand

A calculation small enough to follow on paper shows every step. Take four points with two features: $(2, 0)$, $(0, 2)$, $(4, 2)$, $(2, 4)$.

**Step 1: centre.** The mean of each feature is 2, so subtract $(2, 2)$ from every point. The centred points are $(0,-2)$, $(-2,0)$, $(2,0)$, $(0,2)$.

**Step 2: covariance matrix.** Its diagonal holds each feature's variance (the sum of the squared centred values, divided by $n - 1 = 3$) and the other entries hold the covariance (the sum of the products of the two centred coordinates, divided by 3). In matrix form:

$$C = \frac13 X_c^\top X_c = \frac13\begin{pmatrix}8 & 0\\ 0 & 8\end{pmatrix}.$$

Both variances are equal and the covariance is zero. The points are spread equally in every direction, so *no direction is preferred*: any pair of perpendicular axes is an equally good answer. PCA cannot compress this data. Keeping one dimension loses exactly half of the variance, whichever direction you keep.

Now change the last two points to $(4, 4)$ and $(0, 0)$, so the data is $(2,0)$, $(0,2)$, $(4,4)$, $(0,0)$. The mean is $(1.5, 1.5)$ and the centred points are $(0.5,-1.5)$, $(-1.5,0.5)$, $(2.5,2.5)$, $(-1.5,-1.5)$. The squares of the first coordinates add up to $0.25 + 2.25 + 6.25 + 2.25 = 11$, and the products of the two coordinates add up to $-0.75 - 0.75 + 6.25 + 2.25 = 7$, so

$$C = \frac13\begin{pmatrix}11 & 7\\ 7 & 11\end{pmatrix}.$$

**Step 3: eigenvectors.** An eigenvector of a matrix is a direction that the matrix only stretches, and the stretch factor is its eigenvalue; for a covariance matrix the eigenvectors are the principal directions and the eigenvalues are the variances along them. For a symmetric matrix of the form $\begin{pmatrix}a & b\\ b & a\end{pmatrix}$, the eigenvectors are $(1,1)/\sqrt2$ with eigenvalue $a+b$, and $(1,-1)/\sqrt2$ with eigenvalue $a-b$. (Check the first: multiplying the matrix by $(1, 1)$ gives $(a+b, a+b)$, the same direction scaled by $a+b$.) Here the eigenvalues are $18/3 = 6$ and $4/3 = 1.33$.

**Step 4: explained variance.** The first component accounts for $6/(6 + 1.33) = 81.8\%$ of the variance. Its direction, the diagonal $(1,1)$, is the line along which the points are most spread out.

**Step 5: project.** A centred point's coordinate on the first component is its dot product with $(1,1)/\sqrt2$. For $(4,4)$, centred to $(2.5, 2.5)$, that is $5/\sqrt2 = 3.54$.

```python-run
import numpy as np
from sklearn.decomposition import PCA
X = np.array([[2.0, 0.0], [0.0, 2.0], [4.0, 4.0], [0.0, 0.0]])
Xc = X - X.mean(axis=0)
C = Xc.T @ Xc / (len(X) - 1)
vals, vecs = np.linalg.eigh(C)
print("covariance matrix:\n", C.round(3))
print("eigenvalues:", vals.round(3), " -> explained variance ratio:", (vals[::-1] / vals.sum()).round(3))
pca = PCA(n_components=1).fit(X)
print("sklearn component:", pca.components_[0].round(3), " ratio:", pca.explained_variance_ratio_.round(3))
print("projections:", pca.transform(X).ravel().round(2))
```

The code follows the five steps: centre, build the covariance matrix (it prints 3.667 and 2.333, which are $11/3$ and $7/3$), and get the eigenvalues with `np.linalg.eigh` (1.333 and 6, smallest first). scikit-learn's PCA then gives the same component, $(0.707, 0.707)$, which is $(1,1)/\sqrt2$, the same ratio of 0.818, and a projection of 3.54 for the third point.

The sign of a component is arbitrary: $(1,1)/\sqrt2$ and $(-1,-1)/\sqrt2$ describe the same line. Two libraries, or two versions of one library, may return opposite signs. That is why the problem *ml-pca-svd* fixes a sign convention.

## Summary

- PCA: centre the data, then rotate onto perpendicular directions of greatest variance, found by the SVD. Keep the first $k$. Scale the features first. The components are hard to interpret.
- `explained_variance_ratio_` says how much of the data's spread each component keeps.
- NMF: non-negative, additive parts. Its components have no order and change when you ask for a different number.
- t-SNE: a flexible mapping to two dimensions that keeps neighbours together. Excellent for pictures, but it has no `transform`, and the sizes of and distances between groups cannot be trusted.

## Glossary

- **Dimensionality**: the number of features of a dataset.
- **Dimensionality reduction**: describing each sample with fewer numbers while keeping most of the information.
- **Principal component analysis (PCA)**: rotating the data onto perpendicular directions of greatest variance.
- **Principal component**: one of those directions.
- **Centring**: subtracting each feature's mean.
- **Uncorrelated**: having no straight-line relationship.
- **Explained variance ratio**: the share of the data's total variance that one component accounts for.
- **Loadings**: the weights of the original features in a component (`components_`).
- **Reconstruction**: the approximation of the original data obtained by transforming back from the reduced form.
- **Whitening**: rescaling the principal components to variance 1.
- **Eigenfaces**: the principal components of a set of face images.
- **Non-negative matrix factorisation (NMF)**: writing non-negative data as a sum of non-negative parts.
- **Manifold**: a curved surface inside a high-dimensional space on which the data lies.
- **Embedding**: a position in a low-dimensional space assigned to each sample.
- **t-SNE**: a manifold-learning method for two-dimensional pictures that preserves neighbourhoods.
- **Perplexity**: t-SNE's setting for roughly how many neighbours each point attends to.

## Check yourself

```quiz
[
  {"q": "The first principal component is the direction…", "options": ["along which the data has maximum variance", "that best separates the classes", "of the feature with the largest mean", "orthogonal to all the data"], "answer": 0,
   "explain": "PCA is unsupervised: it looks only at variance, not at labels."},
  {"q": "Why should features usually be standardised before PCA?", "options": ["PCA maximises variance, so features with large units would dominate", "PCA requires non-negative data", "PCA cannot centre data on its own", "To make the components sparse"], "answer": 0,
   "explain": "Variance depends on units; scaling puts features on an equal footing."},
  {"q": "`pca.components_` for PCA(n_components=2) on 30 features has shape…", "options": ["(2, 30)", "(30, 2)", "(2, 2)", "(30, 30)"], "answer": 0,
   "explain": "Each row is one principal direction expressed in the original feature space."},
  {"q": "A key difference between NMF and PCA is that in NMF…", "options": ["components and coefficients are non-negative, giving additive parts", "components are orthogonal", "components are sorted by explained variance", "the result is independent of the random seed"], "answer": 0,
   "explain": "Non-negativity prevents cancellation, which often yields more interpretable parts."},
  {"q": "Which statement about t-SNE is TRUE?", "options": ["It cannot transform new, unseen data points", "Distances between clusters in the plot are reliable", "It is a linear projection", "It requires labels"], "answer": 0,
   "explain": "t-SNE has only fit_transform; it is for exploration. Global distances and cluster sizes are not meaningful."},
  {"q": "With whiten=True, PCA additionally…", "options": ["rescales the projected components to unit variance", "removes the mean twice", "makes the data non-negative", "sorts the samples"], "answer": 0,
   "explain": "Whitening divides each component by its standard deviation, like applying StandardScaler after the rotation."},
  {"q": "PCA(n_components=0.95) means…", "options": ["keep as many components as needed to explain 95% of the variance", "keep 95% of the features", "use 95% of the samples", "set the learning rate to 0.95"], "answer": 0,
   "explain": "A float between 0 and 1 is interpreted as a target cumulative explained variance."}
]
```

> **Source:** Müller & Guido, *Introduction to Machine Learning with Python*, ch. 3 ("Dimensionality Reduction, Feature Extraction, and Manifold Learning": PCA, eigenfaces, NMF, manifold learning with t-SNE); scikit-learn User Guide, "Decomposing signals in components" and "Manifold learning".
