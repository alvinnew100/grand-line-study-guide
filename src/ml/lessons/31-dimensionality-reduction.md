# Dimensionality reduction: PCA, NMF and t-SNE

Transforming data with unsupervised learning has three common motivations: **visualisation**,
**compression**, and **finding a representation that is more informative** for later processing. This
lesson covers the three algorithms Müller & Guido present: principal component analysis (the workhorse),
non-negative matrix factorisation (for parts-based features) and t-SNE (for 2-D visualisation).

## 1. Principal component analysis (PCA)

PCA **rotates** the dataset so that the rotated features are statistically uncorrelated. The rotation is
often followed by keeping only a subset of the new features, chosen by how important they are for
explaining the data.

The algorithm, in words:

1. Find the direction of **maximum variance**. This direction holds the most information, and it is
   *component 1*.
2. Find the direction with the most variance among those **orthogonal** to the first. This is *component 2*.
3. Continue until you have as many components as features.

The directions are the **principal components**. To transform, subtract the mean (so the data is centred
at zero) and rotate so that the components line up with the axes. In the rotated data the features are
uncorrelated. To reduce dimension, keep only the first $k$ components.

### The maths

With centred data $X_c$ and the SVD $X_c = USV^\top$:

- the principal directions are the rows of $V^\top$ (`pca.components_`, shape `(k, p)`);
- the projected data are $Z = X_cV_k = U_kS_k$ (`pca.transform(X)`);
- the variance of component $j$ is $s_j^2/(n-1)$ (`explained_variance_`), and
  `explained_variance_ratio_` is $s_j^2/\sum_i s_i^2$;
- the reconstruction is $\hat X = ZV_k^\top + \bar x$ (`inverse_transform`). Among all rank-$k$ linear
  projections, this one has the smallest squared reconstruction error.

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

### PCA for visualisation

The breast-cancer dataset has 30 features, which makes 435 possible pairwise scatter plots. PCA lets you
look at one 2-D picture that captures the main interactions. **Scale first**, because PCA finds directions
of maximum variance and a feature with large units would dominate.

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

PCA never saw the labels, yet the two classes separate well along the first component. Even a linear
classifier in this 2-D space would do reasonably well. The downside the book notes: **the axes are hard to
interpret**. Each component is a combination of all 30 original features, and the coefficients in
`components_` (the *loadings*) mix them together.

### How many components?

Look at the cumulative explained variance, or let scikit-learn choose: `PCA(n_components=0.95)` keeps
enough components to explain 95% of the variance.

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

### PCA for feature extraction: eigenfaces

The book's second application uses face images (Labeled Faces in the Wild). Pixels are a poor
representation: comparing two images pixel by pixel breaks down if a face shifts by one pixel. With
`PCA(n_components=100, whiten=True)`, each face is expressed as a weighted sum of 100 "eigenfaces".
**Whitening** rescales the components to unit variance. A 1-nearest-neighbour classifier then improved
from about 23% to about 31% accuracy on 62 people. The components capture things like lighting direction
and contrast between face and background. They are not how a human perceives faces, but they give a more
useful distance measure. The small digits dataset below is already centred and aligned, so raw pixels work
well there and PCA does not improve accuracy. What it shows is **compression**: 16 numbers per image keep
almost all of the accuracy of 64 pixels.

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

> [!INTERVIEW]
> **"Explain PCA and its limits."** It is a linear, unsupervised method that finds orthogonal directions of
> maximum variance (the eigenvectors of the covariance matrix, computed by SVD of the centred data). It is
> used for compression, de-correlation, noise reduction and visualisation. Limits: it is linear only; it
> is sensitive to scaling and outliers; the directions of highest variance are not necessarily the most
> *predictive* ones, because it ignores labels; and the components are hard to interpret.

## 2. Non-negative matrix factorisation (NMF)

NMF also writes each data point as a weighted sum of components, $X \approx WH$. But it requires both the
**components and the coefficients to be non-negative**. It therefore applies only to data where every
feature is non-negative, such as pixel intensities, word counts or audio spectrograms.

Why this helps: with no negative weights, components cannot cancel each other out. The result is an
**additive, parts-based** decomposition that is often **more interpretable** than PCA. This is especially
true for data made by overlaying independent sources, such as several people talking or music with many
instruments. On the faces data, NMF components look like face *parts* and prototypes (faces turned left,
faces turned right) instead of PCA's global light/dark patterns.

Differences from PCA that the book points out:

- There is no ordering of components. All play an equal part, and none is "first".
- **Changing the number of components changes all of them.** NMF with 15 components is not a subset of NMF
  with 20, unlike PCA.
- NMF uses random initialisation, so results depend on the seed.
- It is used mostly for finding patterns, less for reconstruction or encoding.

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

Other decomposition methods the book points to: independent component analysis (ICA), factor analysis
(FA) and sparse coding (dictionary learning).

## 3. Manifold learning with t-SNE

PCA is often a good first step for visualisation, but being a rotation, it is limited. **Manifold
learning** algorithms allow far more complex mappings and often give better pictures. The best known is
**t-SNE** (t-distributed stochastic neighbour embedding).

How it works: t-SNE starts with a random 2-D position for each point, then moves the points so that points
**close in the original space stay close** and points far apart stay far apart. It puts much more weight on
preserving *neighbours* than on preserving large distances. Technically, it turns distances into
neighbour probabilities in both spaces and minimises the KL divergence between them. It uses a
heavy-tailed Student-t distribution in the low-dimensional space, which gives clusters room to spread out.

Properties to remember:

- It only has `fit_transform`. There is **no `transform` for new data**, so it is for exploratory
  visualisation, not for preprocessing a test set.
- It is completely unsupervised, yet on the handwritten digits it separates the ten classes far more
  cleanly than the first two principal components do.
- Tuning parameters are `perplexity` (roughly the neighbourhood size; 5–50 is the typical range) and
  `early_exaggeration`. The defaults usually work.
- **Reading t-SNE plots**: cluster *sizes* and the *distances between clusters* mean little, and different
  seeds give different layouts. Only the neighbourhood structure is trustworthy.
- It is slow for large $n$. A common trick is to reduce to about 50 dimensions with PCA first. **UMAP** is
  a popular faster alternative.

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

## 4. Choosing a method

| goal | method |
|---|---|
| compress or de-correlate features before a model | PCA (in a pipeline, fitted on training data) |
| quick linear 2-D look at the data | PCA |
| interpretable additive parts from non-negative data | NMF |
| the best 2-D picture of cluster structure | t-SNE or UMAP (exploration only) |
| sparse high-dimensional text counts | `TruncatedSVD` (PCA without centring, keeps sparsity) |

## 5. Worked example: PCA on four points by hand

A calculation small enough to follow on paper shows every step. Take four 2-D points:
$(2, 0)$, $(0, 2)$, $(4, 2)$, $(2, 4)$.

**Step 1: centre.** The mean is $(2, 2)$. The centred points are $(0,-2)$, $(-2,0)$, $(2,0)$, $(0,2)$.

**Step 2: covariance matrix.** With $n-1 = 3$ in the denominator,

$$C = \frac13 X_c^\top X_c = \frac13\begin{pmatrix}8 & 0\\ 0 & 8\end{pmatrix}.$$

Both variances are equal and the covariance is zero. The data is spread equally in every direction, so
*no direction is preferred*: any pair of orthogonal axes is a valid answer. PCA cannot compress this
data. Reducing to one dimension loses exactly half of the variance, whichever direction you keep.

Now move the last two points to $(4, 4)$ and $(0, 0)$, so the data is $(2,0)$, $(0,2)$, $(4,4)$, $(0,0)$.
The mean is $(1.5, 1.5)$ and

$$C = \frac13\begin{pmatrix}11 & 5\\ 5 & 11\end{pmatrix}.$$

**Step 3: eigenvectors.** For a symmetric matrix of the form $\begin{pmatrix}a & b\\ b & a\end{pmatrix}$
the eigenvectors are $(1,1)/\sqrt2$ with eigenvalue $a+b$ and $(1,-1)/\sqrt2$ with eigenvalue $a-b$.
Here the eigenvalues are $16/3$ and $6/3$.

**Step 4: explained variance.** The first component explains $16/(16+6) = 72.7\%$ of the variance. Its
direction, the diagonal $(1,1)$, is the line along which the points are most spread out.

**Step 5: project.** The coordinate of a centred point on the first component is its dot product with
$(1,1)/\sqrt2$. For $(4,4)$, centred to $(2.5, 2.5)$, that is $5/\sqrt2 = 3.54$.

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

The sign of a component is arbitrary: $(1,1)/\sqrt2$ and $(-1,-1)/\sqrt2$ describe the same line. Two
libraries, or two versions of one library, may return opposite signs. That is why problem *ml-pca-svd*
fixes a sign convention.

## Summary

- PCA: centre, then rotate onto orthogonal directions of maximum variance (SVD). Keep the top $k$. Scale
  first. The components are hard to interpret.
- `explained_variance_ratio_` tells you how much information each component keeps.
- NMF: non-negative, additive parts. Components are unordered and change with their number.
- t-SNE: a nonlinear embedding that preserves neighbours. Excellent for visualisation, but it has no
  `transform` and its global geometry cannot be trusted.

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
