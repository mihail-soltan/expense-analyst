import pandas as pd
import matplotlib.pyplot as plt

class Visualizer:
    def __init__(
        self,
        monthly_total_spending_trend,
        weekly_total_spending_trend,
        monthly_spending_breakdown_by_category,
        overall_category_expense_proportions,
        transaction_frequency_vs_avg_spend_size_by_month
    ):
        self.monthly_total_spending_trend=monthly_total_spending_trend
        self.weekly_total_spending_trend=weekly_total_spending_trend
        self.monthly_spending_breakdown_by_category=monthly_spending_breakdown_by_category
        self.overall_category_expense_proportions=overall_category_expense_proportions
        self.transaction_frequency_vs_avg_spend_size_by_month=transaction_frequency_vs_avg_spend_size_by_month

    def convert_to_df(self, query_result, columns_list):
        df = pd.DataFrame(query_result)
        df.columns = columns_list
        return df 
    
    def plot_monthly_total_spending_trend(self):
        fig, ax = plt.subplots(1, figsize = (20, 8))
        ax.grid()
        fig.autofmt_xdate()
        monthly_total_spending_trend_df = self.convert_to_df(self.monthly_total_spending_trend, ["month", "total_spending"])
        plt.plot(monthly_total_spending_trend_df['month'], 
            monthly_total_spending_trend_df['total_spending'], 
            marker='o')
        path = "figures/monthly_total_spending_trend.png"
        fig.savefig(path, format="png", bbox_inches="tight")
        plt.close(fig)
        return path

    def plot_weekly_total_spending_trend(self):
        fig, ax = plt.subplots(1, figsize = (20, 8))
        ax.grid()
        fig.autofmt_xdate()
        weekly_total_spending_trend_df = self.convert_to_df(self.weekly_total_spending_trend, ["week", "total_spending"])
        plt.fill_between(weekly_total_spending_trend_df['week'], 
        weekly_total_spending_trend_df['total_spending'], 
        alpha=0.3)
        path = "figures/weekly_total_spending_trend.png"
        fig.savefig(path, format="png", bbox_inches="tight")
        plt.close(fig)
        return path
    
    def plot_monthly_spending_breakdown_by_category(self):
        monthly_spending_breakdown_by_category_df = self.convert_to_df(self.monthly_spending_breakdown_by_category, ["month", "category", "total_spending"])
        ax = monthly_spending_breakdown_by_category_df.pivot(index='month', columns='category', values='total_spending').plot(kind='bar', stacked=True).legend(bbox_to_anchor=(1.5, 1))
        fig = ax.get_figure()
        path = "figures/monthly_spending_breakdown_by_category.png"
        fig.savefig(path, format="png", bbox_inches="tight")
        plt.close(fig)
        return path
    
    def plot_overall_category_expense_proportions(self):
        fig, ax = plt.subplots(1, figsize = (20, 8))
        ax.grid()
        fig.autofmt_xdate()
        overall_category_expense_proportions_df = self.convert_to_df(self.overall_category_expense_proportions, ["category", "total_spending", "percentage"])
        plt.pie(overall_category_expense_proportions_df['total_spending'], labels=overall_category_expense_proportions_df['category'], autopct='%1.1f%%')
        path="figures/overall_category_expense_proportions.png"
        fig.savefig(path, format="png", bbox_inches="tight")
        plt.close(fig)
        return path
    
    def plot_transaction_frequency_vs_avg_spend_size_by_month(self):
        transaction_frequency_vs_avg_spend_size_by_month_df = self.convert_to_df(self.transaction_frequency_vs_avg_spend_size_by_month, ["month", "transaction_count", "avg_transaction_amount"])
        fig, ax1 = plt.subplots(1, figsize = (20, 8))
        ax1.grid()
        fig.autofmt_xdate()
        color_bars = '#4C72B0' 
        ax1.bar(transaction_frequency_vs_avg_spend_size_by_month_df['month'], 
                transaction_frequency_vs_avg_spend_size_by_month_df['transaction_count'], 
                color=color_bars, 
                alpha=0.8, 
                label='Transaction Count'
                )

        ax1.set_xlabel('Month', fontweight='bold', labelpad=10)
        ax1.set_ylabel('Transaction Count', color=color_bars, fontweight='bold', labelpad=10)
        ax1.tick_params(axis='y', labelcolor=color_bars)
        ax1.tick_params(axis='x', rotation=45)

        ax2 = ax1.twinx()

        color_line = '#C44E52'
        ax2.plot(transaction_frequency_vs_avg_spend_size_by_month_df['month'], 
                 transaction_frequency_vs_avg_spend_size_by_month_df['avg_transaction_amount'], 
                 color=color_line, 
                 marker='o', 
                 linewidth=2.5, 
                 markersize=8, 
                 label='Avg Transaction Amount')
        ax2.set_ylabel('Average Transaction Amount ($)', color=color_line, fontweight='bold', labelpad=10)
        ax2.tick_params(axis='y', labelcolor=color_line)

        plt.title('Transaction Frequency vs. Average Spend Size by Month', fontsize=14, fontweight='bold', pad=15)
        ax1.grid(axis='y', linestyle='--', alpha=0.3)

        lines_1, labels_1 = ax1.get_legend_handles_labels()
        lines_2, labels_2 = ax2.get_legend_handles_labels()
        ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper left', frameon=True)
        
        path = "figures/transaction_frequency_vs_avg_spend_size_by_month.png"
       
        fig.tight_layout()
        fig.savefig(path, format="png", bbox_inches="tight")
        plt.close(fig)
        return path 