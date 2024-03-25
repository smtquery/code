import tkinter as tk
from tkinter import messagebox
import joblib
import numpy as np
import os
import smtquery.config
class InputBox:
    def __init__(self, master):
        self.master = master
        master.title("Input")

        # Eingabefelder mit Standardwert 0
        self.entries = {}
        self.variables = [
            "numStringVar", "varRatio", "numWEQ", "numQWEQ", "maxNumOfQVar", "scopeIncidence",
            "largestRatioVarCon", "smallestRatioVarCon", "largestRatioLR", "smallestRatioLR",
            "numReg", "maxSymb", "maxDepth", "maxNumState", "numLin", "numAsserts", "maxRecDepth",
            "LenConVars", "WEQVars", "WeqLenVars", "numITE"
        ]

        for var in self.variables:
            row = tk.Frame(master)
            row.pack(side=tk.TOP, fill=tk.X, padx=5, pady=5)
            label = tk.Label(row, width=20, text=var, anchor='w')
            entry = tk.Entry(row)
            entry.insert(tk.END, "0")  # Standardwert 0 einfügen
            label.pack(side=tk.LEFT)
            entry.pack(side=tk.RIGHT, expand=tk.YES, fill=tk.X)
            self.entries[var] = entry

        # Button zur Ausführung der Vorhersage
        self.predict_button = tk.Button(master, text="Prediction", command=self.predict)
        self.predict_button.pack(side=tk.TOP, padx=5, pady=5)

    def predict(self):
        # Laden des Random Forest-Modells
        try:
            rf_model = joblib.load("random_forest.joblib")
        except FileNotFoundError:
            messagebox.showerror("Error", "Model not found!")
            return

        # Extrahieren der Eingabewerte und Konvertieren in float
        input_values = []
        for var in self.variables:
            try:
                input_values.append(float(self.entries[var].get()))
            except ValueError:
                messagebox.showerror("Error", f"Invalid value {var}!")
                return

        # Durchführen der Vorhersage
        input_values = np.array(input_values).reshape(1, -1)
        prediction = rf_model.predict(input_values)
        solver = ['Z3Str3', 'Z3Seq', 'CVC5', 'CVC4', 'Ostrich']
        # Anzeige der Vorhersage in einer Box
        messagebox.showinfo("Prediction", f" {solver[prediction[0]]}")

def main():
    root = tk.Tk()
    input_box = InputBox(root)
    root.mainloop()

if __name__ == "__main__":
    main()
