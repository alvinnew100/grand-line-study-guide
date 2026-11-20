TRACK = dict(
    id="ml",
    title="Machine Learning",
    icon="🧠",
    color="#7b5ea7",
    group="Machine Learning & MLOps",
    blurb="From the maths underneath to scikit-learn models, evaluation, pipelines, text, deep-learning essentials "
          "and interview-ready system design — with runnable code in every lesson and 25 numpy implementation problems.",
    sources=[
        "Müller & Guido, Introduction to Machine Learning with Python (O'Reilly), ch. 1–8",
        "scikit-learn User Guide (scikit-learn.org)",
        "Chip Huyen, AI Engineering (O'Reilly) — background for deep learning and system design",
        "Goodfellow, Bengio & Courville, Deep Learning — background for the maths and optimisers",
    ],
    modules=[
        dict(
            id="math",
            title="0 · Math Foundations for ML",
            summary="Vectors, matrices, SVD; derivatives, gradients and the chain rule; probability, MLE and bias-variance.",
            lessons=[
                dict(id="linear-algebra", title="Linear algebra for ML", file="00-linear-algebra.md"),
                dict(id="calculus-optimization", title="Calculus, gradients and gradient descent", file="01-calculus-optimization.md"),
                dict(id="probability-statistics", title="Probability, statistics and MLE", file="02-probability-statistics.md"),
            ],
            problems=["ml-mse-mae", "ml-cosine-similarity", "ml-softmax"],
        ),
        dict(
            id="intro",
            title="1 · Introduction to Machine Learning",
            summary="What ML is, the kinds of learning, the scikit-learn estimator API and a first model on iris.",
            lessons=[
                dict(id="what-is-ml", title="What machine learning is (and isn't)", file="10-what-is-ml.md"),
                dict(id="sklearn-first-model", title="The scikit-learn API and your first model", file="11-sklearn-first-model.md"),
            ],
            problems=["ml-train-test-split", "ml-knn-predict"],
        ),
        dict(
            id="supervised",
            title="2 · Supervised Learning",
            summary="Generalisation, k-NN, linear models, naive Bayes, trees and ensembles, kernel SVMs, neural networks, uncertainty.",
            lessons=[
                dict(id="generalization-knn", title="Generalisation, overfitting and k-NN", file="20-generalization-knn.md"),
                dict(id="linear-models", title="Linear models: regression, ridge, lasso, logistic", file="21-linear-models.md"),
                dict(id="bayes-trees-ensembles", title="Naive Bayes, decision trees and ensembles", file="22-bayes-trees-ensembles.md"),
                dict(id="svm-mlp-uncertainty", title="Kernel SVMs, neural networks and uncertainty", file="23-svm-mlp-uncertainty.md"),
            ],
            problems=["ml-sigmoid-bce", "ml-normal-equation", "ml-gd-linear-regression", "ml-logreg-gradient",
                      "ml-gini-best-split", "ml-info-gain", "ml-mlp-forward", "ml-mlp-backprop"],
        ),
        dict(
            id="unsupervised",
            title="3 · Unsupervised Learning & Preprocessing",
            summary="Scaling, PCA, NMF, t-SNE, k-means, agglomerative clustering, DBSCAN and how to evaluate clusters.",
            lessons=[
                dict(id="preprocessing-scaling", title="Preprocessing and scaling", file="30-preprocessing-scaling.md"),
                dict(id="dimensionality-reduction", title="PCA, NMF and t-SNE", file="31-dimensionality-reduction.md"),
                dict(id="clustering", title="Clustering: k-means, agglomerative, DBSCAN", file="32-clustering.md"),
            ],
            problems=["ml-standard-scaler", "ml-pca-svd", "ml-kmeans-step"],
        ),
        dict(
            id="features",
            title="4 · Representing Data & Feature Engineering",
            summary="One-hot encoding, binning, interactions, polynomials, nonlinear transforms and feature selection.",
            lessons=[
                dict(id="feature-engineering", title="Categorical features, binning and polynomials", file="40-feature-engineering.md"),
                dict(id="feature-selection", title="Nonlinear transforms, feature selection and expert knowledge", file="41-feature-selection.md"),
            ],
            problems=["ml-one-hot"],
        ),
        dict(
            id="evaluation",
            title="5 · Model Evaluation & Improvement",
            summary="Cross-validation strategies, grid search, and the metrics that matter: precision, recall, ROC, PR, regression.",
            lessons=[
                dict(id="cross-validation", title="Cross-validation", file="50-cross-validation.md"),
                dict(id="grid-search", title="Grid search and nested cross-validation", file="51-grid-search.md"),
                dict(id="metrics", title="Evaluation metrics and imbalanced data", file="52-metrics.md"),
            ],
            problems=["ml-kfold-indices", "ml-confusion-matrix", "ml-precision-recall-f1", "ml-roc-auc"],
        ),
        dict(
            id="pipelines",
            title="6 · Algorithm Chains & Pipelines",
            summary="Pipeline and make_pipeline, grid-searching pipelines, ColumnTransformer and avoiding data leakage.",
            lessons=[
                dict(id="pipelines", title="Pipelines and grid search", file="60-pipelines.md"),
                dict(id="columntransformer-leakage", title="ColumnTransformer and data leakage", file="61-columntransformer-leakage.md"),
            ],
            problems=["ml-impute-scale-pipeline"],
        ),
        dict(
            id="text",
            title="7 · Working with Text Data",
            summary="Bag of words, tf-idf, n-grams, tokenisation, stemming/lemmatisation and topic modelling with LDA.",
            lessons=[
                dict(id="bag-of-words", title="Bag of words, tf-idf and n-grams", file="70-bag-of-words.md"),
                dict(id="tokenization-topics", title="Tokenisation, normalisation and topic models", file="71-tokenization-topics.md"),
            ],
            problems=["ml-tfidf"],
        ),
        dict(
            id="deep-learning",
            title="8 · Deep Learning Essentials",
            summary="Tensors and the PyTorch training loop, optimisers and regularisation, CNNs, RNNs, embeddings and attention.",
            lessons=[
                dict(id="training-loop", title="Tensors, autograd and the training loop", file="80-training-loop.md"),
                dict(id="optimizers-regularization", title="Optimisers and regularisation", file="81-optimizers-regularization.md"),
                dict(id="architectures", title="CNNs, RNNs, embeddings and attention", file="82-architectures.md"),
            ],
            problems=["ml-adam-step", "ml-attention"],
        ),
        dict(
            id="interview",
            title="9 · ML Interviews & System Design",
            summary="The questions interviewers actually ask, and a framework for ML system design rounds.",
            lessons=[
                dict(id="interview-essentials", title="ML interview essentials", file="90-interview-essentials.md"),
                dict(id="system-design", title="ML system design primer", file="91-system-design.md"),
            ],
            problems=[],
        ),
    ],
)
