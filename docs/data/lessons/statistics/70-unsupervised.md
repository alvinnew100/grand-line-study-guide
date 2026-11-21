# Unsupervised learning: PCA and clustering, the statistical view

> **Before this lesson:** standardisation and z-scores from [Normal, t and long-tailed distributions](#/lesson/statistics/normal-t-long-tails), covariance and correlation matrices from [Correlation and exploring two or more variables](#/lesson/statistics/correlation-bivariate), and the normal model with a covariance matrix from [Naive Bayes and discriminant analysis](#/lesson/statistics/naive-bayes-lda). The ML track covers the scikit-learn side in [PCA, NMF and t-SNE](#/lesson/ml/dimensionality-reduction) and [Clustering: k-means, agglomerative, DBSCAN](#/lesson/ml/clustering); here we focus on what the methods assume and how to judge their output.

## In plain words

So far every model had an outcome to predict. **Unsupervised learning** has no outcome: it looks for structure in the predictors themselves. **Principal components analysis** (PCA) finds a few combinations of many correlated variables that capture most of their variation, compressing the data. **Clustering** groups records that are similar to each other, for example customer segments. Because there is no "right answer" to check against, the statistical questions are about assumptions (scale, shape, distance) and about choosing how many components or clusters to keep.

An everyday picture: a wardrobe. PCA is noticing that most of the variety in your clothes comes down to two things, formality and warmth, so you could describe every item with two numbers instead of ten. Clustering is sorting the clothes into piles (gym, office, winter) without anyone telling you the categories in advance.

Why it matters for a job: segmentation, dimensionality reduction before modelling, anomaly detection and exploratory analysis all rely on these tools. Interviewers ask: "Why standardise before PCA?", "How do you choose k in k-means?", "What are k-means' assumptions?", "How would you cluster customers with both numeric and categorical attributes?"

## 1. Principal components analysis

Given $p$ numeric variables, PCA finds new variables called **principal components** (PCs), each a weighted sum of the originals:

$$PC_1 = w_{11}X_1 + w_{12}X_2 + \dots + w_{1p}X_p$$

The weights are called **loadings**. PC1 is the direction along which the data vary most; PC2 is the direction of greatest remaining variation that is uncorrelated with (perpendicular to) PC1; and so on, up to $p$ components. Mathematically, the loadings are the eigenvectors of the covariance (or correlation) matrix, and each component's variance is the corresponding eigenvalue. In practice PCA is computed with the **singular value decomposition** (SVD), which factors the centred data matrix as $U S V^T$: the rows of $V^T$ are the loadings and the squared singular values in $S$ are proportional to the variances.

We simulate daily returns of five stocks: four driven by a common "market" factor and a "tech" factor (two stocks positively, two negatively), and one mostly independent stock.

```python-run
import numpy as np
rng = np.random.default_rng(70)
n = 500
market = rng.normal(0, 1, n)
tech = rng.normal(0, 1, n)
returns = np.column_stack([
    0.9 * market + 0.4 * tech + rng.normal(0, 0.3, n),
    0.8 * market + 0.5 * tech + rng.normal(0, 0.3, n),
    0.9 * market - 0.3 * tech + rng.normal(0, 0.3, n),
    0.8 * market - 0.4 * tech + rng.normal(0, 0.3, n),
    0.1 * market + rng.normal(0, 0.5, n),
])
Z = (returns - returns.mean(axis=0)) / returns.std(axis=0)
U, S, Vt = np.linalg.svd(Z, full_matrices=False)
explained = S**2 / np.sum(S**2)
print("explained variance ratio:", np.round(explained, 3))
print("loadings PC1:", np.round(Vt[0], 3))
print("loadings PC2:", np.round(Vt[1], 3))
```

**Reading this code line by line**

- `np.column_stack` builds a 500 × 5 table of returns from the two hidden factors plus noise.
- `Z` standardises each column (subtract its mean, divide by its standard deviation), so PCA works on the correlation structure.
- `np.linalg.svd(Z, full_matrices=False)` returns $U$, the singular values $S$ and $V^T$.
- `S**2 / np.sum(S**2)` is the **explained variance ratio**: each component's share of the total variance.

PC1 explains 61% of the variance and loads roughly equally on the four related stocks (about $-0.5$ each) and barely on the fifth: it is the market factor. PC2 explains another 20% and is dominated by the independent fifth stock. Together, two components summarise 81% of the information in five columns. (The sign of a component is arbitrary: your run may show PC1's loadings all positive, which means the same thing.)

### Choosing the number of components

- A **scree plot** shows explained variance by component; keep those before the curve flattens (the "elbow"). Here the drop after the third component (0.156 to 0.017) is sharp.
- Keep enough components to explain a target share, such as 80% or 90%.
- If PCA feeds a predictive model, choose the number by cross-validating that model.

### Always think about scale

PCA follows variance, so variables measured in large units dominate. Standardise unless the variables share meaningful units.

```python-run
import numpy as np
from sklearn.decomposition import PCA
rng = np.random.default_rng(71)
n = 400
a = rng.normal(0, 1, n)
X = np.column_stack([a * 1000 + rng.normal(0, 300, n), a + rng.normal(0, 1, n), rng.normal(0, 1, n)])
print("raw PCA, explained:", np.round(PCA().fit(X).explained_variance_ratio_, 4))
Xs = (X - X.mean(axis=0)) / X.std(axis=0)
print("standardised PCA, explained:", np.round(PCA().fit(Xs).explained_variance_ratio_, 4))
```

**Reading this code line by line**

- The first column is in large units (think dollars); the second is a related variable in small units; the third is noise.
- `PCA().fit(X).explained_variance_ratio_` runs PCA with scikit-learn.

On raw data PC1 explains essentially 100% of the variance and is nothing but the dollar column. After standardising, the shares are 0.56, 0.33 and 0.11, revealing that two variables share a factor and the third is independent.

PCA is used to compress correlated features before regression (principal components regression), to visualise high-dimensional data in two dimensions, to build indices (a single "market" score), and to detect anomalies (records poorly reconstructed from the top components). For categorical data, **correspondence analysis** plays a similar role.

## 2. K-means clustering

**K-means** divides records into $K$ clusters so as to minimise the **within-cluster sum of squares**: the total squared distance from each record to its cluster's mean (its **centroid**). The algorithm alternates two steps until assignments stop changing:

1. Assign each record to the nearest centroid.
2. Move each centroid to the mean of its assigned records.

It converges to a local minimum, so it is run from several random starts (`n_init`) and the best result kept.

K-means' implicit assumptions: clusters are roughly spherical (round, equally spread in every direction), of similar size and spread, and distances are meaningful, which again means standardising variables in different units.

### Choosing K

```python-run
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
rng = np.random.default_rng(72)
centres = np.array([[0, 0], [5, 0], [2.5, 4]])
X = np.vstack([rng.normal(c, 1.0, size=(150, 2)) for c in centres])
for k in range(2, 7):
    km = KMeans(n_clusters=k, n_init=10, random_state=0).fit(X)
    print(f"k={k}: within-cluster SS {km.inertia_:8.1f}  silhouette {silhouette_score(X, km.labels_):.3f}")
```

**Reading this code line by line**

- Three round groups of 150 points are generated around three centres.
- `KMeans(n_clusters=k, n_init=10)` runs k-means from 10 random starts; `.inertia_` is the within-cluster sum of squares.
- `silhouette_score` averages, over all records, how much closer each record is to its own cluster than to the next nearest cluster (from $-1$ to 1; higher is better).

The within-cluster sum of squares always falls as $K$ grows (to zero at one cluster per record), so look for the **elbow**: it drops from 2,518.8 to 855.6 going from 2 to 3 clusters, then only gradually. The silhouette peaks clearly at $K = 3$ (0.609). In real data the elbow is often vague; choose $K$ by combining such measures with interpretability and usefulness (can marketing act on 4 segments? on 12?), and check stability by re-running on bootstrap samples.

## 3. Hierarchical clustering

**Agglomerative hierarchical clustering** starts with every record as its own cluster and repeatedly merges the two closest clusters, producing a tree of merges called a **dendrogram**. Cutting the tree at a chosen height gives any number of clusters, which makes it good for exploring how groups nest. The key choice is the **linkage**, how distance between two clusters is defined:

- **Single**: distance between the closest pair of members. Tends to "chain" clusters together.
- **Complete**: distance between the farthest pair. Produces compact clusters.
- **Average**: mean distance between all pairs.
- **Ward**: merge the pair that increases within-cluster sum of squares least (like k-means).

```python-run
import numpy as np
from scipy.cluster.hierarchy import linkage, fcluster
from sklearn.metrics import adjusted_rand_score
rng = np.random.default_rng(73)
centres = np.array([[0, 0], [5, 0], [2.5, 4]])
X = np.vstack([rng.normal(c, 1.0, size=(100, 2)) for c in centres])
truth = np.repeat([0, 1, 2], 100)
for method in ["single", "complete", "average", "ward"]:
    labels = fcluster(linkage(X, method=method), t=3, criterion="maxclust")
    sizes = np.bincount(labels)[1:]
    print(f"{method:8s} cluster sizes {sizes}  agreement with truth (ARI) {adjusted_rand_score(truth, labels):.3f}")
```

**Reading this code line by line**

- `linkage(X, method=...)` from SciPy computes the full merge history; `fcluster(..., t=3, criterion="maxclust")` cuts it into 3 clusters.
- `np.bincount(labels)[1:]` counts records per cluster (SciPy numbers clusters from 1).
- `adjusted_rand_score` compares the clustering with the true groups: 1 is perfect agreement, about 0 is chance.

Single linkage chains everything into one giant cluster with two stragglers (sizes 298, 1, 1; agreement 0). Complete linkage recovers the groups reasonably (0.894); average and Ward linkage almost perfectly (0.980). Hierarchical clustering compares all pairs of records, so it is slow for large datasets (memory grows with $n^2$); k-means scales far better.

## 4. Model-based clustering

**Model-based clustering** assumes the data come from a mixture of probability distributions, typically multivariate normals (a **Gaussian mixture model**), each with its own mean and covariance matrix. Fitting (by an algorithm called expectation-maximisation) estimates the parameters and each record's probability of belonging to each cluster ("soft" assignment). Because clusters can be elongated and tilted, it handles shapes k-means cannot, and because it is a statistical model, the number of clusters can be chosen with BIC.

```python-run
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_rand_score
rng = np.random.default_rng(74)
g1 = rng.multivariate_normal([0, 0], [[6, 5.5], [5.5, 6]], 300)
g2 = rng.multivariate_normal([0, 4], [[6, 5.5], [5.5, 6]], 300)
X = np.vstack([g1, g2]); truth = np.repeat([0, 1], 300)
for k in range(1, 5):
    gm = GaussianMixture(n_components=k, covariance_type="full", random_state=0).fit(X)
    print(f"{k} components: BIC {gm.bic(X):8.1f}")
gm = GaussianMixture(2, covariance_type="full", random_state=0).fit(X)
km = KMeans(2, n_init=10, random_state=0).fit(X)
print(f"ARI Gaussian mixture {adjusted_rand_score(truth, gm.predict(X)):.3f}, k-means {adjusted_rand_score(truth, km.labels_):.3f}")
```

**Reading this code line by line**

- Two long, tilted, parallel clouds are generated (strong correlation 5.5/6 within each), offset vertically.
- `GaussianMixture(n_components=k, covariance_type="full")` lets each component have its own full covariance matrix; `.bic(X)` returns the Bayesian information criterion (lower is better).
- We compare the agreement with the truth of a 2-component mixture and of 2-cluster k-means.

BIC is lowest at 2 components (5,317.5), correctly identifying the number of groups. The Gaussian mixture recovers them well (ARI 0.921), while k-means, which wants round clusters, slices across the elongated clouds and gets only 0.181. The cost of model-based clustering: more parameters, slower fitting, and dependence on the normal assumption.

## 5. Scaling and mixed data types

Clustering is only as good as its distance measure:

- **Standardise numeric variables** so that no variable dominates because of its units. Sometimes you deliberately weight important variables more.
- **Binary and categorical variables** do not fit Euclidean distance well. One-hot encoding them and standardising gives rare categories outsized influence.
- **Gower's distance** handles mixed types by computing a distance between 0 and 1 for each variable and averaging: for numeric variables, the absolute difference divided by the variable's range; for categorical ones, 0 if equal and 1 if different.

```python-run
import numpy as np
import pandas as pd
customers = pd.DataFrame({
    "age": [25, 47, 31, 62],
    "spend": [120.0, 900.0, 150.0, 400.0],
    "plan": ["basic", "pro", "basic", "team"],
    "mobile": [True, False, True, False],
})
num, cat = ["age", "spend"], ["plan", "mobile"]
ranges = customers[num].max() - customers[num].min()
def gower(i, j):
    parts = [abs(customers.at[i, c] - customers.at[j, c]) / ranges[c] for c in num]
    parts += [float(customers.at[i, c] != customers.at[j, c]) for c in cat]
    return np.mean(parts)
D = np.array([[gower(i, j) for j in range(4)] for i in range(4)])
print(np.round(D, 3))
```

**Reading this code line by line**

- Four customers with two numeric and two categorical attributes.
- `ranges` holds each numeric variable's range; `customers.at[i, c]` reads one cell.
- `gower(i, j)` averages the per-variable distances; the nested list comprehension builds the full 4 × 4 distance matrix.

Customers 0 and 2 (young, low spend, basic plan, mobile) are almost identical (0.05); customer 1 (older, high spend, pro, desktop) is far from both (about 0.85 to 0.9). The resulting matrix can feed hierarchical clustering (`linkage` accepts precomputed distances in condensed form) or k-medoids, a k-means variant that uses actual records as centres and works with any distance.

## 6. Judging an unsupervised result

- Is the result **stable**? Re-run on bootstrap samples or different random starts; segments that dissolve are not real.
- Are the clusters **interpretable** and **actionable**? Profile each by its means and category shares.
- Are the clusters driven by **one variable**? Check scaling.
- Does it **help downstream**? For example, do segment-specific campaigns outperform a single campaign in an A/B test?

> [!INTERVIEW]
> "How would you segment our users?" Define the purpose first (marketing, product, pricing); choose behavioural features; clean and standardise (log-transform skewed counts); handle categorical attributes with Gower's distance or careful encoding; try k-means for a quick baseline and a Gaussian mixture if clusters may be elongated; choose $K$ with silhouette or BIC plus business interpretability; validate stability; then test whether segment-specific actions beat a uniform approach.

## Summary

- PCA finds uncorrelated weighted combinations of variables that capture the most variance; loadings describe them; explained variance ratios and scree plots guide how many to keep.
- Standardise before PCA and clustering unless variables share units.
- K-means minimises within-cluster sum of squares and assumes round, similar clusters; choose $K$ with the elbow, silhouette, interpretability and stability.
- Hierarchical clustering builds a dendrogram; the linkage (single, complete, average, Ward) changes the result greatly.
- Gaussian mixture models handle elongated clusters, give soft assignments, and choose the number of clusters by BIC.
- Gower's distance handles mixed numeric and categorical data.

## Glossary

- **Unsupervised learning**: finding structure in data without an outcome variable.
- **Principal components analysis (PCA) / principal component**: finding variance-maximising uncorrelated combinations / one such combination.
- **Loadings**: the weights defining a principal component.
- **Singular value decomposition (SVD)**: a matrix factorisation used to compute PCA.
- **Explained variance ratio / scree plot**: a component's share of total variance / a chart of those shares.
- **Clustering**: grouping similar records.
- **K-means / centroid**: clustering by minimising squared distances to cluster means / a cluster mean.
- **Within-cluster sum of squares (inertia)**: total squared distance of records to their centroids.
- **Elbow method / silhouette score**: choosing K where improvement flattens / a measure of cluster separation.
- **Agglomerative hierarchical clustering / dendrogram**: repeatedly merging closest clusters / the tree of merges.
- **Linkage (single, complete, average, Ward)**: rules for the distance between clusters.
- **Adjusted Rand index (ARI)**: agreement between two clusterings, corrected for chance.
- **Model-based clustering / Gaussian mixture model**: clustering by fitting a mixture of distributions / a mixture of normals.
- **Gower's distance**: a distance for mixed data types averaging per-variable distances scaled to [0, 1].
- **K-medoids**: a k-means variant using actual records as centres.

## Check yourself

```quiz
[
  {"q": "Why standardise variables before PCA when they are measured in different units?", "options": ["PCA follows variance, so large-unit variables would dominate the components", "PCA requires normal data", "It makes the components uncorrelated", "It reduces the number of components to one"], "answer": 0,
   "explain": "The raw-data demo gave PC1 100% of variance from the dollar column alone."},
  {"q": "PC1 explains 61% and PC2 20% of variance. Keeping both summarises about…", "options": ["81% of the total variance", "61%", "20%", "41%"], "answer": 0,
   "explain": "Components are uncorrelated, so their explained shares add."},
  {"q": "The within-cluster sum of squares in k-means…", "options": ["always decreases as K increases, so look for an elbow", "is minimised at K = 2", "increases with K", "is unaffected by K"], "answer": 0,
   "explain": "More clusters always fit at least as tightly; the elbow marks diminishing returns."},
  {"q": "Two long, tilted, parallel clusters are best separated by…", "options": ["a Gaussian mixture with full covariance", "k-means", "single-linkage hierarchical clustering", "PCA alone"], "answer": 0,
   "explain": "Full-covariance mixtures model elongated shapes; k-means assumes round clusters."},
  {"q": "Single-linkage hierarchical clustering tends to…", "options": ["chain clusters together into one large cluster", "produce perfectly round clusters", "ignore distances", "always match k-means"], "answer": 0,
   "explain": "Joining on the closest pair lets clusters connect through stray points."},
  {"q": "You must cluster customers by age, spend, plan type and device. A suitable distance is…", "options": ["Gower's distance", "Euclidean distance on raw values", "Correlation between customers", "The Gini impurity"], "answer": 0,
   "explain": "Gower's distance scales numeric differences by range and treats categories as match or mismatch."}
]
```

> **Source:** Bruce & Bruce, *Practical Statistics for Data Scientists* (O'Reilly, 2017), ch. 7, "Principal Components Analysis" (computing and interpreting principal components), "K-Means Clustering" (selecting the number of clusters), "Hierarchical Clustering" (dendrogram, agglomerative algorithm, measures of dissimilarity), "Model-Based Clustering" (multivariate normal, mixtures, selecting the number of clusters) and "Scaling and Categorical Variables" (Gower's distance); scikit-learn and SciPy documentation.
