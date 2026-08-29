import json
from rag_helper import RAGBase, SQLStringList
from sqlite3 import OperationalError
from sqlite_db import get_db_connection

class RAGEvaluator(RAGBase):
    def __init__(
            self,
            *args,
            **kwargs
    ):
        super().__init__(*args, **kwargs)

        self.is_valid = []
        self.execution_accuracy_rate_list = []

        self.evaluation = {
            "valid_execution_rate": None,
            "execution_accuracy": None
        }

    def is_sql_valid(self, query_list):

        is_valid = []
        query_results = []
    
        for q in query_list:
            try:
                result = self.execute_query(q["sql"])
                query_results.extend(result)
                is_valid.append(1)
    
            except OperationalError as e:
                print("Invalid SQL: ", e)
                is_valid.append(0)
    
        return is_valid, query_results

    def get_ground_truth_results(self, query):
        ground_truth_results = []
        result = self.execute_query(query)
        ground_truth_results.extend(result)
        return ground_truth_results

    def calculate_stat(self, results):
        """
        This method takes a list of 1s and 0s and divides the sum of all the elements by the length of the list. 
        It can be used to measure execution accuracy or valid execution rate
        """
        return sum(results)/len(results)

    def compare_query_results(self, flat_query_results, flat_ground_truth_results):
        """
        This function takes two flat lists of dictionaries, converts each dictionary to a set.
        if either set is a subset of its counterpart, a 1 will be appended to the execution accuracy rate list, otherwise a 0 will be appended.
        """
        execution_accuracy_rate_list = []

        for el in range(len(flat_query_results)):
            query_result_set = set(flat_query_results[el].values())
            ground_truth_result_set = set(flat_ground_truth_results[el].values())
            if query_result_set.issubset(ground_truth_result_set) or ground_truth_result_set.issubset(query_result_set):
                execution_accuracy_rate_list.append(1)
            else:
                execution_accuracy_rate_list.append(0)
        return execution_accuracy_rate_list

    def flatten_list(self, list):
        return sum(list, [])

    def get_sql_results(self, doc):
        """
        This function returns: 
        - a list `is_valid` containing numbers from 0 to 1. for each query executed successfully a 1 is returned, for each error - 0
        - a list of dictionaries containing results based on the queries returned by the llm 
        - a list of results based on the ground truth queries. These are then used to compare to the llm query_results  
        """

        question = doc["question"]
        ground_truth_query = doc["ground_truth_sql"]
        response = self.llm_structured_response(question, schema=SQLStringList.model_json_schema())
        output = json.loads(response.output_text)
        query_list = output["queries"]
        is_valid, query_results = self.is_sql_valid(query_list)
        ground_truth_results = self.get_ground_truth_results(ground_truth_query)


        return is_valid, query_results, ground_truth_results

    def evaluate(self, results):
        """
        This 
        """
        is_valid = []

        for result in results:
            is_valid_result = result[0]
            query_result = result[1]
            ground_truth_result = result[2]

            is_valid.append(is_valid_result)
            if len(query_result) != len(ground_truth_result):
                self.execution_accuracy_rate_list.append(0)
            else:
                comparison = self.compare_query_results(query_result, ground_truth_result)
                if all(comparison):
                    self.execution_accuracy_rate_list.append(1)
                else:
                    self.execution_accuracy_rate_list.append(0)

        self.is_valid = self.flatten_list(is_valid)
    
        self.evaluation["valid_execution_rate"] = self.calculate_stat(self.is_valid)
        self.evaluation["execution_accuracy"] = self.calculate_stat(self.execution_accuracy_rate_list)