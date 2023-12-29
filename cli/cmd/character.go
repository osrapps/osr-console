package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

var character = &cobra.Command{
	Use:   "character {create|delete|list|show}",
	Short: "Manage player characters.",
	Long:  `Create, delete, list, and show player characters and their attributes.`,
	Run: func(cmd *cobra.Command, args []string) {
		fmt.Println("Character command executed")
	},
}

func init() {
	rootCmd.AddCommand(character)
}
