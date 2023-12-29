package cmd

import (
	"github.com/spf13/cobra"
)

var rootCmd = &cobra.Command{
	Use:   "osr",
	Short: "The command-line interface to osrlib.",
	Long:  `The 'osr' CLI provides command-line access to osrlib and its rules engine.`,
}

func Execute() error {
	return rootCmd.Execute()
}

func init() {
	// TODO: Define flags and configuration settings.
	//
	// Persistent flag example:
	// rootCmd.PersistentFlags().StringVar(&cfgFile, "config", "", "config file (default is $HOME/.myapp.yaml)")
	//
	// Local flag example:
	// rootCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
