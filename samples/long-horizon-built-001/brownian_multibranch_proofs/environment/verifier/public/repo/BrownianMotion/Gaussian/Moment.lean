module

public import Mathlib.Probability.Distributions.Gaussian.Real

@[expose] public section

open MeasureTheory
open scoped NNReal

namespace ProbabilityTheory

lemma centralMoment_two_mul_gaussianReal (μ : ℝ) (σ : ℝ≥0) (n : ℕ) :
    centralMoment id (2 * n) (gaussianReal μ (σ^2))
    = σ ^ (2 * n) * Nat.doubleFactorial (2 * n - 1) := /- BEGIN TASK PROOF centralMoment_two_mul_gaussianReal -/
by
  sorry
/- END TASK PROOF centralMoment_two_mul_gaussianReal -/

lemma centralMoment_fun_two_mul_gaussianReal (μ : ℝ) (σ : ℝ≥0) (n : ℕ) :
    centralMoment (fun x ↦ x) (2 * n) (gaussianReal μ (σ^2))
    = σ ^ (2 * n) * Nat.doubleFactorial (2 * n - 1) :=
  centralMoment_two_mul_gaussianReal ..

end ProbabilityTheory
