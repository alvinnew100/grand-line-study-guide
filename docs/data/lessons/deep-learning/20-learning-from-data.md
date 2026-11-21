# Learning as parameter estimation: loss and gradient descent

> **Before this lesson:** you need tensors, shapes and broadcasting from [Tensors: creation, indexing, dtypes and broadcasting](#/lesson/deep-learning/tensors-basics), and standardisation from [Real-world data as tensors](#/lesson/deep-learning/data-as-tensors). The idea of a derivative (the slope of a curve) is re-explained here; for a slower treatment see [Calculus, gradients and gradient descent](#/lesson/ml/calculus-optimization).

## In plain words

Every learning algorithm in this track, from a two-number model to a billion-parameter network, does the same thing: it has a formula with adjustable numbers (the **parameters**), it measures how wrong the formula's outputs are on known examples (the **loss**), and it repeatedly nudges the parameters in the direction that makes the loss smaller. That nudging procedure is **gradient descent**. Learning is nothing more than **parameter estimation**: searching for the parameter values that best explain the data.

Think of tuning an old radio with two knobs, coarse and fine, while listening to static. You turn one knob slightly; if the static decreases you keep turning that way, if it increases you turn back. You do this for both knobs, over and over, taking smaller turns as the signal gets clear. Gradient descent is that procedure, done with arithmetic instead of ears, for every knob at once.

Why it matters for a job: if you can derive and code gradient descent for a tiny model by hand, you understand what `loss.backward()` and `optimizer.step()` do in every PyTorch program. Interviewers routinely ask you to implement this loop in NumPy, explain why a loss explodes, or explain why inputs must be normalised. This lesson builds all of it from scratch on a problem small enough to see every number.

## 1. A problem small enough to see

A taxi company in a new city publishes no tariff. You collect ten receipts showing trip distance in kilometres and fare in dollars, and you suspect the meter uses a fixed flag-down fee plus a rate per kilometre. In symbols:

$$\text{fare} = w \cdot \text{distance} + b$$

Here $w$ (the **weight**, dollars per kilometre) and $b$ (the **bias**, the flag-down fee) are the unknown parameters. This is a **linear model**: a straight line. We want the $w$ and $b$ that make the line pass as close as possible to the ten receipts. The receipts are slightly noisy (rounding, waiting time), so no line fits perfectly.

The plan is general and you will reuse it all track long:

1. Choose a **model**: a formula with parameters.
2. Choose a **loss function**: one number measuring how far the model's predictions are from the truth.
3. Compute how the loss changes when each parameter changes (the **gradient**).
4. Update the parameters a little against the gradient; repeat.

## 2. The loss function

For each receipt $i$ with distance $x_i$ and true fare $y_i$, the model predicts $\hat{y}_i = w x_i + b$ (the hat means "predicted"). The error is $\hat{y}_i - y_i$. We combine the errors into one number with the **mean squared error (MSE)**:

$$L(w, b) = \frac{1}{n} \sum_{i=1}^{n} (\hat{y}_i - y_i)^2$$

Why squares rather than plain differences? Positive and negative errors would cancel if we added them raw. Squaring makes every error count positively, punishes big misses much more than small ones, and gives a smooth bowl-shaped function whose lowest point is easy to find. Taking absolute values instead (the **mean absolute error**) also avoids cancellation and is less sensitive to outliers, but it has a sharp corner at zero that makes the slope jump.

```python-run
import numpy as np

distance = np.array([1.2, 2.5, 3.1, 4.8, 5.5, 7.0, 8.2, 9.9, 12.4, 15.0])   # km
fare     = np.array([4.6, 5.9, 6.5, 7.6, 8.6, 9.6, 10.7, 12.6, 14.3, 17.2])  # dollars

def model(x, w, b):
    return w * x + b                      # broadcasting: one prediction per receipt

def loss_fn(pred, target):
    return ((pred - target) ** 2).mean()  # mean squared error

for w, b in [(1.0, 0.0), (1.0, 3.0), (0.9, 3.5), (0.5, 6.0)]:
    print(f"w={w:4.1f}  b={b:4.1f}  ->  loss {loss_fn(model(distance, w, b), fare):7.3f}")
```

Each guess gives one loss value. The guess $w = 0.9, b = 3.5$ is far better than the others. We could keep guessing, but with millions of parameters guessing is hopeless. We need a direction.

## 3. Which way is downhill? The gradient

Picture the loss as a landscape: the two horizontal directions are $w$ and $b$, and the height is $L(w, b)$. For MSE on a linear model the landscape is a smooth bowl. We stand somewhere on it and want to walk downhill.

The **derivative** of a function with respect to one input is its slope in that direction: how much the output changes per tiny change of the input. With several inputs we take one derivative per input while holding the others fixed; these are **partial derivatives**, written $\partial L / \partial w$. The list of all partial derivatives is the **gradient**, written $\nabla L$. It points in the direction of steepest *increase*, so we step the opposite way.

### Estimating the slope by experiment

The most direct way to estimate a slope: nudge a parameter by a tiny amount $\varepsilon$ (epsilon) up and down and see how the loss changes.

$$\frac{\partial L}{\partial w} \approx \frac{L(w + \varepsilon, b) - L(w - \varepsilon, b)}{2\varepsilon}$$

This is a **central finite difference**. It needs two loss evaluations per parameter, so it is far too slow for real networks, but it is perfect for *checking* a gradient you derived another way. That check is called a **gradient check**.

### Computing the slope exactly with the chain rule

Calculus gives the exact formula. The **chain rule** says that if $L$ depends on $\hat{y}$, and $\hat{y}$ depends on $w$, then the slope of $L$ with respect to $w$ is the product of the two slopes:

$$\frac{\partial L}{\partial w} = \sum_i \frac{\partial L}{\partial \hat{y}_i} \cdot \frac{\partial \hat{y}_i}{\partial w}$$

Each piece is easy. From $L = \frac{1}{n}\sum (\hat{y}_i - y_i)^2$ we get $\partial L / \partial \hat{y}_i = \frac{2}{n}(\hat{y}_i - y_i)$. From $\hat{y}_i = w x_i + b$ we get $\partial \hat{y}_i / \partial w = x_i$ and $\partial \hat{y}_i / \partial b = 1$. Therefore

$$\frac{\partial L}{\partial w} = \frac{2}{n}\sum_i (\hat{y}_i - y_i)\, x_i, \qquad \frac{\partial L}{\partial b} = \frac{2}{n}\sum_i (\hat{y}_i - y_i)$$

This "multiply local slopes along the chain" idea is exactly what **backpropagation** does for networks with many layers, and what PyTorch automates in the [next lesson](#/lesson/deep-learning/autograd).

```python-run
import numpy as np

distance = np.array([1.2, 2.5, 3.1, 4.8, 5.5, 7.0, 8.2, 9.9, 12.4, 15.0])
fare     = np.array([4.6, 5.9, 6.5, 7.6, 8.6, 9.6, 10.7, 12.6, 14.3, 17.2])
model = lambda x, w, b: w * x + b
loss_fn = lambda p, y: ((p - y) ** 2).mean()

def grad_fn(x, y, w, b):
    pred = model(x, w, b)
    dL_dpred = 2 * (pred - y) / x.size          # slope of the loss w.r.t. each prediction
    return (dL_dpred * x).sum(), dL_dpred.sum() # chain rule: times d(pred)/dw = x, d(pred)/db = 1

w, b, eps = 1.0, 0.0, 1e-4
num_w = (loss_fn(model(distance, w + eps, b), fare) - loss_fn(model(distance, w - eps, b), fare)) / (2 * eps)
num_b = (loss_fn(model(distance, w, b + eps), fare) - loss_fn(model(distance, w, b - eps), fare)) / (2 * eps)
ana_w, ana_b = grad_fn(distance, fare, w, b)
print(f"dL/dw  finite difference {num_w:10.5f}   chain rule {ana_w:10.5f}")
print(f"dL/db  finite difference {num_b:10.5f}   chain rule {ana_b:10.5f}")
```

**Reading this code line by line**

- `grad_fn` first computes predictions, then the slope of the loss with respect to each prediction, `2 (pred - y) / n`.
- Multiplying by `x` and summing gives $\partial L/\partial w$; summing alone gives $\partial L/\partial b$.
- The finite-difference estimates, computed by nudging $w$ and $b$ by $10^{-4}$, agree with the formulas to many decimal places. Agreement is the evidence that the formula and code are correct.
- Both gradients are **negative** at $w = 1, b = 0$: increasing either parameter would *decrease* the loss, because the line currently sits below the receipts for short trips.

## 4. Taking steps: gradient descent

The update rule moves every parameter against its gradient, scaled by the **learning rate** $\eta$ (eta):

$$w \leftarrow w - \eta \frac{\partial L}{\partial w}, \qquad b \leftarrow b - \eta \frac{\partial L}{\partial b}$$

One pass of "predict, compute loss, compute gradient, update" over the data is one **epoch** here (with all ten receipts used at every step, this is **full-batch gradient descent**). We repeat for many epochs.

```python-run
import numpy as np

distance = np.array([1.2, 2.5, 3.1, 4.8, 5.5, 7.0, 8.2, 9.9, 12.4, 15.0])
fare     = np.array([4.6, 5.9, 6.5, 7.6, 8.6, 9.6, 10.7, 12.6, 14.3, 17.2])
model = lambda x, w, b: w * x + b
loss_fn = lambda p, y: ((p - y) ** 2).mean()

def grad_fn(x, y, w, b):
    d = 2 * (model(x, w, b) - y) / x.size
    return (d * x).sum(), d.sum()

def training_loop(x, y, lr, epochs, report):
    w, b = 1.0, 0.0
    for epoch in range(1, epochs + 1):
        gw, gb = grad_fn(x, y, w, b)        # backward: gradients
        w, b = w - lr * gw, b - lr * gb      # optimizer step
        if epoch in report:
            print(f"  epoch {epoch:5d}  loss {loss_fn(model(x, w, b), y):12.4f}  w {w:8.4f}  b {b:8.4f}")
    return w, b

print("learning rate 0.01:")
training_loop(distance, fare, 0.01, 3000, {1, 10, 100, 1000, 3000})
print("learning rate 0.02 (too large):")
training_loop(distance, fare, 0.02, 10, {1, 2, 4, 6, 8, 10})
print("closed-form least squares for comparison:", np.polyfit(distance, fare, 1).round(4))
```

**What the output shows**

- With learning rate 0.01, the loss falls quickly at first and then slowly; after about 2,000 epochs $w$ settles near 0.892 dollars per kilometre and $b$ near 3.549 dollars, matching the exact least-squares answer computed by `np.polyfit`.
- With learning rate 0.02, the loss grows every epoch and the parameters swing with increasing size: **divergence**. Each step overshoots the bottom of the bowl and lands higher on the opposite side.
- The slow tail at learning rate 0.01 is caused by the two parameters needing very different step sizes, explained next.

## 5. Why scale matters: normalising inputs

Look at the gradient formulas again. $\partial L/\partial w$ contains a factor $x_i$ (distances up to 15), while $\partial L/\partial b$ does not. So the gradient for $w$ is several times larger than the one for $b$ (about six times at our starting point: $-35.1$ versus $-5.6$). A single learning rate must be small enough not to overshoot in the $w$ direction, which then makes progress in the $b$ direction painfully slow. In landscape terms, the bowl is a long narrow valley: steep across, nearly flat along.

If we had recorded distances in metres (values up to 15,000), the imbalance would be a thousand times worse, and no single learning rate would work well. The cure is to **standardise the input** (subtract its mean, divide by its standard deviation) so it is on the scale of 1. The valley becomes a round bowl and gradient descent heads almost straight to the bottom.

```python-run
import numpy as np

distance = np.array([1.2, 2.5, 3.1, 4.8, 5.5, 7.0, 8.2, 9.9, 12.4, 15.0])
fare     = np.array([4.6, 5.9, 6.5, 7.6, 8.6, 9.6, 10.7, 12.6, 14.3, 17.2])
mu, sd = distance.mean(), distance.std()
x = (distance - mu) / sd                            # standardised input

w, b, lr = 1.0, 0.0, 0.1
for epoch in range(1, 101):
    d = 2 * (w * x + b - fare) / x.size
    w, b = w - lr * (d * x).sum(), b - lr * d.sum()
    if epoch in (1, 10, 50, 100):
        print(f"epoch {epoch:3d}  loss {((w * x + b - fare) ** 2).mean():8.4f}")

# Convert back to the original units: fare = w * (dist - mu)/sd + b
w_orig, b_orig = w / sd, b - w * mu / sd
print(f"rate per km {w_orig:.4f}, flag-down fee {b_orig:.4f}")
print("prediction for a 20 km trip: $", round(w_orig * 20 + b_orig, 2))
```

With the standardised input, a learning rate ten times larger is stable and the loss reaches its minimum within about 50 epochs instead of roughly 2,000. Converting back gives the same rate and fee as before. Remember to apply the same `mu` and `sd` to every future input, which is why they are saved with the model.

> [!TIP]
> The general lesson: in a network, every layer's input is some other layer's output, so keeping *all* intermediate values on a sensible scale matters too. That is the job of careful [initialisation and normalisation layers](#/lesson/deep-learning/normalisation-init).

## 6. The same loop in PyTorch

PyTorch computes the gradient for you (autograd) and applies the update for you (an optimizer). Here is the full loop; each line maps onto a line of the NumPy version.

```python
import torch

x = torch.tensor(distance, dtype=torch.float32)
y = torch.tensor(fare, dtype=torch.float32)
x = (x - x.mean()) / x.std(unbiased=False)        # standardise (population std, like NumPy)

params = torch.tensor([1.0, 0.0], requires_grad=True)  # [w, b], track gradients
optimizer = torch.optim.SGD([params], lr=0.1)

for epoch in range(100):
    pred = params[0] * x + params[1]               # forward
    loss = ((pred - y) ** 2).mean()                # loss
    optimizer.zero_grad()                          # clear old gradients
    loss.backward()                                # fills params.grad with dL/dw, dL/db
    optimizer.step()                               # params -= lr * params.grad
```

- `requires_grad=True` asks autograd to record every operation on `params`.
- `loss.backward()` computes the same two gradients our `grad_fn` did, by the chain rule, automatically.
- `optimizer.step()` performs `params -= lr * params.grad`. `SGD` stands for **stochastic gradient descent**; it becomes "stochastic" when each step uses a random subset of the data, covered in the [optimisers lesson](#/lesson/deep-learning/optimizers-validation).
- `zero_grad()` is required because PyTorch **adds** new gradients to `.grad` rather than replacing them.

## 7. When the bowl is not a bowl

For a linear model with squared error, the loss landscape is **convex**: shaped like a single bowl with one lowest point, so gradient descent with a sensible learning rate always finds the best answer. Neural networks are **non-convex**: their landscapes have many valleys, flat plateaus and saddle points. Gradient descent then finds *a* good low point, not provably the best one. In practice, for large networks most low points found are about equally good, and the real challenges become speed, stability and **generalisation** (doing well on new data rather than memorising the training data). Those challenges motivate most of the rest of this track.

> [!INTERVIEW]
> **"Your loss goes up every iteration. What happened and what do you try?"** The learning rate is too large: each step overshoots the minimum and lands higher. Lower it (typically by a factor of 3 to 10), check that inputs are standardised (unscaled features force tiny learning rates and make divergence likely), verify the gradient with a finite-difference check on a tiny case, and make sure the sign of the update is a subtraction. If the loss turns into `nan`, the same causes apply, plus numerical problems such as taking the log of zero.

## 8. An old recipe that still works

The idea of learning parameters from data is older than computers. When Johannes Kepler worked out the laws of planetary motion in the early 1600s, he had no theory telling him the answer: he had Tycho Brahe's careful observations and a lot of patience. His process is a good checklist for any model you fit today:

1. **Get good data**, and more of it than you think you need.
2. **Look at it** before modelling: plot it, so that the shape suggests a family of models.
3. **Try the simplest model that could fit** (Kepler tried circles before he settled on ellipses).
4. **Hold some data back** and check that the fitted model predicts observations it was not fitted on.
5. **Iterate**: when predictions miss in a systematic way, change the model family, not just the numbers.

Gradient descent automates the "adjust the numbers" part of step 3. Steps 1, 2, 4 and 5 remain your job, and skipping them is how models end up fitting noise. The lesson [A complete image classifier](#/lesson/deep-learning/image-classifier) and the validation material that follows turn step 4 into routine practice.

## Summary

- Learning is parameter estimation: choose a model, a loss, compute gradients, step against them.
- MSE averages squared errors; it is smooth and punishes large misses.
- The gradient is the list of partial derivatives; the chain rule multiplies local slopes, which is what backpropagation automates.
- Finite differences estimate gradients slowly but reliably; use them to check analytic gradients.
- Gradient descent: `param -= lr * grad`. Too large a learning rate diverges; too small crawls.
- Standardising inputs balances gradient sizes across parameters and lets you use a larger, stable learning rate.
- Linear least squares is convex; neural networks are not, which shifts the challenge to speed, stability and generalisation.

## Glossary

- **Parameter estimation**: finding parameter values that best explain data.
- **Linear model**: output = weight × input + bias.
- **Loss function**: one number measuring how wrong predictions are.
- **Mean squared error (MSE) / mean absolute error (MAE)**: average of squared / absolute errors.
- **Derivative / partial derivative**: slope of a function / slope with respect to one input holding others fixed.
- **Gradient**: the vector of all partial derivatives; points uphill.
- **Chain rule**: the slope of a composition is the product of the slopes along the chain.
- **Finite difference / gradient check**: estimating a slope by nudging an input / comparing analytic gradients with that estimate.
- **Gradient descent**: repeatedly subtracting learning rate × gradient.
- **Learning rate**: the step-size multiplier in gradient descent.
- **Epoch**: one pass over the training data.
- **Full-batch gradient descent**: each step uses all training examples.
- **Divergence**: the loss growing without bound because steps overshoot.
- **Convex**: having a single bowl-shaped minimum.
- **Generalisation**: performing well on data not seen during training.

## Check yourself

```quiz
[
  {"q": "For the model pred = w·x + b with MSE loss, what is ∂L/∂b?", "options": ["(2/n) Σ (pred − y)", "(2/n) Σ (pred − y)·x", "Σ x", "(1/n) Σ y"], "answer": 0,
   "explain": "∂pred/∂b = 1, so the chain rule leaves the derivative of the loss with respect to each prediction, summed."},
  {"q": "The loss increases at every step and the parameters oscillate with growing size. Most likely cause?", "options": ["The learning rate is too large", "The learning rate is too small", "The data are standardised", "The model is linear"], "answer": 0,
   "explain": "Each step overshoots the minimum; reduce the learning rate."},
  {"q": "Why does standardising the input speed up gradient descent for w·x + b?", "options": ["It balances the gradient sizes of w and b so one learning rate suits both", "It removes noise from the labels", "It makes the model non-linear", "It reduces the number of parameters"], "answer": 0,
   "explain": "Raw large x makes ∂L/∂w much bigger than ∂L/∂b, creating a narrow valley."},
  {"q": "What is a central finite difference used for in deep learning practice?", "options": ["Checking that analytically computed gradients are correct", "Training large networks efficiently", "Choosing the batch size", "Normalising inputs"], "answer": 0,
   "explain": "It needs two loss evaluations per parameter: too slow for training, ideal for verification."},
  {"q": "In PyTorch, why call optimizer.zero_grad() each iteration?", "options": ["backward() adds to existing .grad values", "It resets the parameters", "It sets the learning rate", "It moves data to the GPU"], "answer": 0,
   "explain": "Gradients accumulate by design; without zeroing, each step would use the sum of all previous gradients."},
  {"q": "Why do we square the errors instead of adding them directly?", "options": ["So positive and negative errors cannot cancel, and large errors count more", "Squares are faster to compute", "To make the loss negative", "Because predictions are always positive"], "answer": 0,
   "explain": "Raw errors of +5 and −5 would sum to zero despite two bad predictions."},
  {"q": "Which statement about neural network loss landscapes is accurate?", "options": ["They are non-convex, so gradient descent finds a good low point rather than a guaranteed global minimum", "They are always convex", "They have exactly one minimum", "Gradient descent cannot be used on them"], "answer": 0,
   "explain": "Non-convexity is why initialisation, learning rates and normalisation matter so much."}
]
```

> **Source:** Stevens, Antiga & Viehmann, *Deep Learning with PyTorch*, ch. 5 (learning as parameter estimation, choosing a loss, gradient descent, analytic gradients and the chain rule, the training loop, learning rate and input normalisation); PyTorch documentation, `torch.optim.SGD`.
