import csv
from datetime import datetime
from pijp.repositories import BaseRepository
from pijp import dbprocs
from pijp.dbprocs import format_string_parameter as fsp


class DTIRepository(BaseRepository):
    def __init__(self):
        super().__init__()
        self.connection.setdb('imaging')

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

    def get_masks_to_qc(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {0}
            AND Process = 'pijp dti'
            AND Step = 'RoiStats'
            AND Outcome = 'Done'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE Project = {0}
                    AND Process = 'pijp dti' 
                    AND Step = 'MaskQC'
                    AND (Outcome = 'pass'
                    OR Outcome = 'Error')
            )
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_edited_masks(self, project):
        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {0}
            AND Process = 'pijp dti'
            AND Step = 'MaskQC'
            AND Outcome = 'edit'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {0}
                AND Process = 'pijp dti'
                AND Step = 'WarpQC'
        """.format(dbprocs.format_string_parameter(project))

        todo = self.connection.fetchall(sql)
        return todo

    def set_roi_stats(self, project_id, code, md, fa, ga, rd, ad):
        sql = r"""
        INSERT INTO pijp_dti (Code, ProjectID, FileName, Measure, Roi, MinVal, MaxVal, MeanVal, StdDev)
        VALUES ({code}, {project_id}, {fname}, {measure}, {roi}, {min}, {max}, {mean}, {sd})
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
                        fname = fsp(m.split('/')[-1])
                        roi = fsp(str(row[0]))
                        min_val = fsp(str(row[1]))
                        max_val = fsp(str(row[2]))
                        mean_val = fsp(str(row[3]))
                        sd = fsp(str(row[5]))
                        median_val = fsp(str(row[4]))
                        volume = fsp(str(row[5]))
                        time = fsp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        formatted_sql = sql.format(code=fsp(code), project_id=project_id, fname=fname, measure=msr,
                                                   roi=roi, min=min_val, max=max_val, mean=mean_val, sd=sd,
                                                   median=median_val, vol=volume, time=time)
                        self.connection.execute_non_query(formatted_sql)

    def get_project_id(self, project):
        sql = r"""
        SELECT ProjectID FROM Projects WHERE ProjectName = {0}
        """.format(fsp(project))

        project_id = self.connection.fetchone(sql)
        return project_id
