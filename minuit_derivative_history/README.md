# MINUIT2 Derivative History

Code to hack Minuit2 to get the history of all first derivatives.

Codes:
1. `Minuit3Minimizer.h` and `Minuit3Minimizer.cxx` are directly copied from `Minuit3Minimizer` in ROOT. In case these two are incompatible with newer versions of ROOT, the only changes needed are renaming all instance of `Minuit2Minimizer` to `Minuit3Minimizer` and to declare a public function in `Minuit3Minimizer.h`:
```
   const ROOT::Minuit2::FunctionMinimum * Minima() const { return fMinimum; }
```
2. `history.h` is an example scipt to store the first derivative history into a ROOT file. It might not compile because I didn't `#include` properly but it should be easy to fix.
3. `minuit.h` shows the ROOT runtime library magic needed to load the custom `Minuit3Minimizer` classes.
