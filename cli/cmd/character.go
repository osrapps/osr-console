package cmd

import (
	"fmt"

	"github.com/spf13/cobra"
)

// firstCmd represents the first command
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

	// Here you will define your flags and configuration settings.

	// Cobra supports Persistent Flags which will work for this command
	// and all subcommands, e.g.:
	// firstCmd.PersistentFlags().String("foo", "", "A help for foo")

	// Cobra supports local flags which will only run when this command
	// is called directly, e.g.:
	// firstCmd.Flags().BoolP("toggle", "t", false, "Help message for toggle")
}
