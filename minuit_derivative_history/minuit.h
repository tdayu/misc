#define HEADER_DIR
#define MYLIB_DIR

void setupMyMinuitMinimizer(){
    gInterpreter->AddIncludePath(HEADER_DIR);
    gInterpreter->Declare("#include \"Minuit3Minimizer.h\"");
    gSystem->AddDynamicPath(MYLIB_DIR);
    gSystem->Load("libMinuit3Minimizer");
    // Use Minuit3 to get better logging for first derivatives
    gPluginMgr->AddHandler("ROOT::Math::Minimizer",
                           "MyMinuitMinimizer",
                           "ROOT::Minuit2::Minuit3Minimizer",
                           "Minuit3Minimizer",
                           "Minuit3Minimizer(const char *)");
}
