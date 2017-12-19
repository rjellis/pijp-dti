import csv

class DTIData:
    def __init__(self, project, code):
        self.code = code
        self.project = project
        self.columns= {
            "ProjectName": project,
            "Code": code,
            "FileName": "NULL",
            "MaskQC": "NULL",
            "WarpQC": "NULL",
            "Measure": "NULL",
            "ROI": "NULL",
            "Min": "NULL",
            "Max": "NULL",
            "Mean": "NULL",
            "SD": "NULL",
        }


    def store(self):
        """
        method should store the results and comments of the qc to the database. QC steps should have their own result
        and comment column.
        """
        pass

    def parse_csv(self, path):

        pass
