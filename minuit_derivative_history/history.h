#include "RooMinimizer.h"
#include "TString.h"
#include "TFile.h"
#include "TTree.h"

#include <iostream>
#include <algorithm>
#include <vector>

void storeFitHistory(const RooMinimizer& minimizer,
                     const TString& filepath){
    const auto minuit = dynamic_cast<const ROOT::Minuit2::Minuit3Minimizer*>(minimizer.fitter()->GetMinimizer());

    if ( minuit == nullptr ){
        std::cout << "Cannot cast to Minuit3" << std::endl;
        std::cout << "Unable to store gradients!" << std::endl;
        return;
    }

    const auto * minima = minuit->Minima();
    const auto& states = minima->States();
    const auto& parameters = minima->UserParameters().Parameters();
    const auto& transformer = minima->UserState().Trafo();

    TFile file(filepath, "recreate");
    TTree value_tree("value", "");
    TTree internal_value_tree("internal_value", "");
    TTree external_grad_tree("external_gradient", "Gradients of parameters in external form.");
    TTree grad_tree("first_derivative", "Gradients of parameters in internal form.");
    TTree grad2_tree("second_derivative", "");
    TTree step_tree("step_size", "");
    TTree history_tree("fit_history", "");

    size_t nParameters = parameters.size();
    std::vector<TString> names;
    std::transform(parameters.begin(), parameters.end(), std::back_inserter(names), [](const ROOT::Minuit2::MinuitParameter& par){ return par.GetName().c_str(); });
    std::vector<double> value_vector(nParameters);
    std::vector<double> internal_value_vector(nParameters);
    std::vector<double> external_grad_vector(nParameters);
    std::vector<double> grad_vector(nParameters);
    std::vector<double> grad2_vector(nParameters);
    std::vector<double> step_size_vector(nParameters);

    for (size_t i = 0; i < nParameters; i++){
        const auto& name = names[i];
        value_tree.Branch(name, &(value_vector[i]), name + "/D");
        internal_value_tree.Branch(name, &(internal_value_vector[i]), name + "/D");
        external_grad_tree.Branch(name, &(external_grad_vector[i]), name + "/D");
        grad_tree.Branch(name, &(grad_vector[i]), name + "/D");
        grad2_tree.Branch(name, &(grad2_vector[i]), name + "/D");
        step_tree.Branch(name, &(step_size_vector[i]), name + "/D");
    }

    double FCN, EDM;
    unsigned int nFCN;

    history_tree.Branch("FCN", &FCN, "FCN/D");
    history_tree.Branch("EDM", &EDM, "EDM/D");
    history_tree.Branch("nFCN", &nFCN, "nFCN/i");

    for (const auto& state : states) {

        const auto& values = state.Parameters().Vec();
        const auto& first_derivatives = state.Gradient().Grad();
        const auto& second_derivatives = state.Gradient().G2();
        const auto& step_sizes = state.Gradient().Gstep();

        for (size_t i = 0; i < nParameters; i++){
            value_vector[i] = transformer.Int2ext(i, values[i]);
            internal_value_vector[i] = values[i];
            external_grad_vector[i] = transformer.DInt2Ext(i, first_derivatives[i]);
            grad_vector[i] = first_derivatives[i];
            grad2_vector[i] = second_derivatives[i];
            step_size_vector[i] = step_sizes[i];
        }
        FCN = state.Fval();
        EDM = state.Edm();
        nFCN = state.NFcn();

        internal_value_tree.Fill();
        value_tree.Fill();
        external_grad_tree.Fill();
        grad_tree.Fill();
        grad2_tree.Fill();
        step_tree.Fill();
        history_tree.Fill();
    }
    value_tree.Write();
    internal_value_tree.Write();
    external_grad_tree.Write();
    grad_tree.Write();
    grad2_tree.Write();
    step_tree.Write();
    history_tree.Write();

    file.Close();
}
