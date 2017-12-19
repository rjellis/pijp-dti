import csv
from pijp.repositories import BaseRepository
from pijp import dbprocs
from pijp.dbprocs import format_string_parameter as fsp


class DTIRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.connection.setdb('imaging')

    def get_step_queue(self, project, process, step):
            sql = r"""
            SELECT 
            ScanCode AS Code
            FROM 
            ProcessingLog pl 
            WHERE Project = {project} 
            AND Process = {process}
            AND Step = {prev_step_name}
            AND (Outcome = 'Done' OR Outcome = 'pass')
            AND ScanCode NOT IN (SELECT 
            ScanCode
            FROM 
            ProcessingLog pl 
            WHERE Project = {project} 
            AND Process = {process} 
            AND Step = {step_name}
            AND (Outcome = 'Done' OR Outcome = 'pass'))
            
            """.format(project=dbprocs.format_string_parameter(project),
                       process=dbprocs.format_string_parameter(process),
                       step_name=dbprocs.format_string_parameter(step.step_name),
                       prev_step_name=dbprocs.format_string_parameter(step.prev_step[0].step_name))

            ready = self.connection.fetchall(sql)
            return ready

    def get_mask_qc_list(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'Preregister'
        AND 
            Outcome = 'Done'
        AND 
            ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE 
                    Project = {0}
                AND 
                    Process = 'dti' 
                AND 
                    Step = 'MaskQC'
                AND 
                    Outcome = 'pass'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_warp_qc_list(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'TensorFit'
        AND 
            Outcome = 'Done'
        AND 
            ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE 
                    Project = {0}
                AND 
                    Process = 'dti' 
                AND 
                    Step = 'WarpQC'
                AND 
                    Outcome = 'pass'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_mask_qced_list(self, project):

        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'MaskQC'
        AND 
            Outcome = 'Pass'
        AND
            ScanCode NOT IN (
            SELECT 
                ScanCode
            FROM 
                ProcessingLog
            WHERE 
                Project = {0}
            AND 
                Step = 'Register'
            AND 
                Outcome = 'Done'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_warp_qced_list(self, project):

        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE 
            Project = {0}
        AND 
            Process = 'dti' 
        AND 
            Step = 'WarpQC'
        AND 
            Outcome = 'Pass'
        AND
            ScanCode NOT IN (
            SELECT 
                ScanCode
            FROM 
                ProcessingLog
            WHERE 
                Project = {0}
            AND 
                Step = 'RoiStats'
            AND 
                Outcome = 'Done'
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_project_dtis(self, project):

        sql = r"""
        SELECT 
            SeriesCode AS Code
        FROM 
            dbo.DicomSeries se
        INNER JOIN
            dbo.DicomStudies st
        ON
            se.StudyInstanceUID = st.StudyInstanceUID
        WHERE 
            st.StudyCode = {project} 
        AND 
            SeriesDescription LIKE '%MR 2D AXIAL DTI BRAIN%'
        """.format(project=fsp(project))

        todo = self.connection.fetchall(sql)
        return todo

    def set_roi_stats(self, table, project, code, md, fa, ga, rd, ad):
        sql = r"""INSERT INTO {table} VALUES ({code}, {project}, {fname}, {measure}, {roi}, {min}, {max}, {mean}, {sd})
        """
        measures = [md, fa, ga, rd, ad]
        for m in measures:
            with open(m) as csvfile:
                mreader = csv.reader(csvfile, delimiter=',')
                msr = fsp(m.split('_')[-2].rstrip('_roi.csv'))
                for row in mreader:
                    roi = fsp(str(row[0]))
                    min = fsp(str(row[1]))
                    max = fsp(str(row[2]))
                    mean = fsp(str(row[3]))
                    sd = fsp(str(row[4]))
                    formatted_sql = sql.format(table=fsp(table), project=fsp(project), fname =fsp(m), code=fsp(code),
                                               measure=msr, roi=roi, min=min, max=max, mean=mean, sd=sd)
                    self.connection.execute_non_query(formatted_sql)
