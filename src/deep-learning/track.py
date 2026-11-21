TRACK = dict(
    id="deep-learning",
    title="Deep Learning with PyTorch",
    icon="🔥",
    color="#ee4c2c",
    group="Machine Learning & MLOps",
    blurb="Tensors, autograd, nn.Module, convnets and a full medical-imaging project (classification, segmentation, "
          "fine-tuning), then modern practice: AdamW, schedules, mixed precision, torch.compile, debugging and export. "
          "Runnable NumPy versions of every building block and 30 implementation problems.",
    sources=[
        "Stevens, Antiga & Viehmann, Deep Learning with PyTorch (Manning), ch. 1–15",
        "PyTorch documentation (docs.pytorch.org): torch.amp, torch.compile, torch.export, torch.onnx, torch.utils.data",
        "Goodfellow, Bengio & Courville, Deep Learning — background for optimisation and regularisation",
    ],
    modules=[
        dict(
            id="foundations",
            title="0 · Deep Learning and PyTorch",
            summary="What deep learning is, why it took over, how PyTorch is organised, and running pretrained models.",
            lessons=[
                dict(id="why-deep-learning", title="What deep learning is and where PyTorch fits", file="00-why-deep-learning.md"),
                dict(id="pretrained-models", title="Running pretrained models: classifiers, GANs and hubs", file="01-pretrained-models.md"),
            ],
            problems=["dl-channel-normalize"],
        ),
        dict(
            id="tensors",
            title="1 · Tensors",
            summary="Creating, indexing and broadcasting tensors; dtypes; storage, strides and views; devices; turning images, tables, time series and text into tensors.",
            lessons=[
                dict(id="tensors-basics", title="Tensors: creation, indexing, dtypes and broadcasting", file="10-tensors-basics.md"),
                dict(id="tensor-storage", title="Under the hood: storage, strides, views and devices", file="11-tensor-storage.md"),
                dict(id="data-as-tensors", title="Real-world data as tensors: images, tables, time series, text", file="12-data-as-tensors.md"),
            ],
            problems=["dl-broadcast-shape", "dl-tensor-view-strides", "dl-one-hot-encode"],
        ),
        dict(
            id="learning",
            title="2 · The Mechanics of Learning",
            summary="Learning as parameter estimation, gradient descent by hand, autograd in depth, torch.optim and validation.",
            lessons=[
                dict(id="learning-from-data", title="Learning as parameter estimation: loss and gradient descent", file="20-learning-from-data.md"),
                dict(id="autograd", title="Autograd in depth: graphs, backward, no_grad and gradient checks", file="21-autograd.md"),
                dict(id="optimizers-validation", title="Optimisers (SGD, momentum, Adam, AdamW) and validation", file="22-optimizers-validation.md"),
            ],
            problems=["dl-linear-gd-fit", "dl-tiny-autograd", "dl-sgd-momentum-step", "dl-adamw-step"],
        ),
        dict(
            id="networks",
            title="3 · Neural Networks with torch.nn",
            summary="Artificial neurons and activation functions; nn.Module, Sequential, parameters, state_dict and checkpoints.",
            lessons=[
                dict(id="neurons-activations", title="Neurons, layers and activation functions", file="23-neurons-activations.md"),
                dict(id="nn-module", title="nn.Module, state_dict and checkpointing", file="24-nn-module.md"),
            ],
            problems=["dl-activation-grads", "dl-linear-backward", "dl-param-count"],
        ),
        dict(
            id="images",
            title="4 · Learning from Images",
            summary="Datasets, transforms and DataLoaders; a fully connected classifier with softmax and cross-entropy; convolutions and pooling.",
            lessons=[
                dict(id="datasets-dataloaders", title="Dataset, transforms and DataLoader (workers, pinning, samplers)", file="30-datasets-dataloaders.md"),
                dict(id="image-classifier", title="A first image classifier: softmax, cross-entropy and its limits", file="31-image-classifier.md"),
                dict(id="convolutions", title="Convolutions, pooling and building a convnet", file="32-convolutions.md"),
            ],
            problems=["dl-minibatch-indices", "dl-log-softmax", "dl-cross-entropy", "dl-conv-output-size",
                      "dl-conv2d-forward", "dl-maxpool2d", "dl-receptive-field"],
        ),
        dict(
            id="model-design",
            title="5 · Model Design",
            summary="Capacity and overfitting; weight decay, dropout and early stopping; batch/layer norm and initialisation; depth and residual connections.",
            lessons=[
                dict(id="regularisation", title="Training a convnet and fighting overfitting", file="34-regularisation.md"),
                dict(id="normalisation-init", title="Normalisation layers and weight initialisation", file="35-normalisation-init.md"),
                dict(id="depth-residuals", title="Going deeper: vanishing gradients and residual connections", file="36-depth-residuals.md"),
            ],
            problems=["dl-dropout", "dl-batchnorm-forward", "dl-early-stopping"],
        ),
        dict(
            id="ct-project",
            title="6 · Project: Finding Lung Nodules in CT Scans",
            summary="A real end-to-end project: CT data, a 3D classifier, metrics for rare positives, balancing, augmentation, U-Net segmentation, fine-tuning.",
            lessons=[
                dict(id="ct-project-plan", title="Planning a large project: CT scans and the five-step pipeline", file="40-ct-project-plan.md"),
                dict(id="ct-data-pipeline", title="From raw CT files to a Dataset", file="41-ct-data-pipeline.md"),
                dict(id="training-application", title="A training application: 3D convnet, logging and TensorBoard", file="42-training-application.md"),
                dict(id="imbalance-metrics", title="Rare positives: precision, recall, F1 and balanced sampling", file="43-imbalance-metrics.md"),
                dict(id="augmentation", title="Overfitting and data augmentation", file="44-augmentation.md"),
                dict(id="segmentation", title="Segmentation with U-Net and Dice loss", file="45-segmentation.md"),
                dict(id="end-to-end-finetuning", title="End to end: grouping, ROC/AUC and fine-tuning", file="46-end-to-end-finetuning.md"),
            ],
            problems=["dl-precision-recall-f1", "dl-class-balanced-weights", "dl-augment-flip-shift", "dl-iou-dice",
                      "dl-connected-components"],
        ),
        dict(
            id="modern-training",
            title="7 · Modern Training Practice",
            summary="Warmup and cosine schedules, gradient clipping, GPU memory, mixed precision, torch.compile, fast data loading and debugging.",
            lessons=[
                dict(id="schedules-clipping", title="Learning-rate schedules, warmup and gradient clipping", file="50-schedules-clipping.md"),
                dict(id="memory-mixed-precision", title="GPU memory and mixed precision (autocast, bf16, GradScaler)", file="51-memory-mixed-precision.md"),
                dict(id="compile-throughput", title="torch.compile, input pipelines and multi-GPU basics", file="52-compile-throughput.md"),
                dict(id="debugging-training", title="Debugging training: overfit one batch, NaNs and gradient checks", file="53-debugging-training.md"),
            ],
            problems=["dl-warmup-cosine-lr", "dl-clip-grad-norm", "dl-grad-scaler"],
        ),
        dict(
            id="deployment",
            title="8 · Serving and Exporting Models",
            summary="Serving behind an HTTP API with request batching; TorchScript (legacy), torch.export, ONNX, C++ and mobile.",
            lessons=[
                dict(id="serving-export", title="Serving and exporting PyTorch models", file="60-serving-export.md"),
            ],
            problems=["dl-request-batching"],
        ),
        dict(
            id="interview",
            title="9 · Deep Learning Interviews",
            summary="The questions interviewers ask about deep learning, and worked coding problems from real rounds.",
            lessons=[
                dict(id="interview-essentials", title="Deep learning interview essentials", file="90-interview-essentials.md"),
                dict(id="interview-problems", title="Deep learning interview problems, worked", file="91-interview-problems.md"),
            ],
            problems=[],
        ),
    ],
)
