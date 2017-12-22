import csv
from datetime import datetime
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
        WHERE Project = {0}
            AND Process = 'dti' 
            AND Step = 'RoiStats'
            AND Outcome = 'Done'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE Project = {0}
                    AND Process = 'dti' 
                    AND Step = 'MaskQC'
                    AND (Outcome = 'pass'
                    OR Outcome = 'edit')
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_project_masks(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {0}
            AND Process = 'dti' 
            AND ((Step = 'MaskQC'
                  AND Outcome = 'edit')
            OR
                (Step = 'Mask'
                 AND Outcome = 'Done'))
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
        WHERE st.StudyCode = {project} 
            AND SeriesDescription LIKE '%MR 2D AXIAL DTI BRAIN%'
        """.format(project=fsp(project))

        todo = self.connection.fetchall(sql)
        return todo

    def set_roi_stats(self, table, project, code, md, fa, ga, rd, ad):
        sql = r"""INSERT INTO {table} (Code, Project, FileName, Measure, Roi, MinVal, MaxVal, MeanVal, 
        StdDev, MedianVal, RecordTime) VALUES ({code}, {project}, {fname}, {measure}, {roi}, {min}, {max}, 
        {mean}, {sd}, {median}, {time})
        """
        measures = [md, fa, ga, rd, ad]
        for m in measures:
            with open(m) as csvfile:
                mreader = csv.reader(csvfile, delimiter=',')
                msr = fsp(m.split('_')[-2].rstrip('_roi.csv'))  # fsp() : dbprocs.format_string_parameters
                for row in mreader:
                    if mreader.line_num == 1:
                        row.pop()
                    else:
                        print(mreader.line_num)
                        roi = fsp(str(row[0]))
                        min_val = fsp(str(row[1]))
                        max_val = fsp(str(row[2]))
                        mean_val = fsp(str(row[3]))
                        median_val = fsp(str(row[4]))
                        sd = fsp(str(row[5]))
                        time = fsp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        formatted_sql = sql.format(table=fsp(table), project=fsp(project), fname=fsp(m),
                                                   time=time, code=fsp(code), measure=msr, roi=roi, min=min_val,
                                                   max=max_val, mean=mean_val, sd=sd, median=median_val)
                        self.connection.execute_non_query(formatted_sql)
