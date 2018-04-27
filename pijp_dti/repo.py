import csv
import getpass
from datetime import datetime

from pijp.dbprocs import format_string_parameter as fsp
from pijp.repositories import BaseRepository
import pijp_dti


PROCESS_TITLE = pijp_dti.__process_title__


class DTIRepo(BaseRepository):

    def __init__(self):
        super().__init__()
        self.connection.setdb('imaging')

    def get_project_id(self, project):
        sql = r"""
        SELECT ProjectID FROM Projects WHERE ProjectName = {}
        """.format(fsp(project))

        project_id = self.connection.fetchone(sql)

        if project_id:
            project_id = project_id["ProjectID"]

        return project_id

    def get_project_settings(self, project):

        sql = r"""
        SELECT
            UseNNICV,
            SaveMNI
        FROM
            ProjectPijpDTI
        WHERE
            ProjectID = {proj_id}
        """.format(proj_id=(self.get_project_id(project)))

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

    def get_staged_cases(self, project):

        sql = r"""
        SELECT
            DISTINCT ScanCode AS Code
        From 
            ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'Stage'
            AND (Outcome = 'Done' OR Outcome = 'Error' OR Outcome = 'Queued')
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_masks_to_qc(self, project):
        sql = r"""
        SELECT DISTINCT 
            ScanCode AS Code
        FROM 
            ProcessingLog pl 
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'Mask'
            AND Outcome = 'Done'
            AND ScanCode NOT IN(
                SELECT 
                    ScanCode
                FROM 
                    ProcessingLog pl 
                WHERE Project = {project}
                    AND Process = {process}
                    AND Step = 'MaskQC'
                    AND (Outcome = 'Pass' OR Outcome = 'Edit' OR Outcome = 'Fail')
            )
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_segs_to_qc(self, project):
        sql = r"""
        SELECT
            ScanCode AS Code
        FROM 
            ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'MaskQC'
            AND Outcome = 'Pass'
            AND ScanCode NOT IN(
                SELECT
                    ScanCode
                FROM
                    ProcessingLog
                WHERE Project = {project}
                AND Process = {process}
                AND Step = 'SegQC'
                AND (Outcome = 'Pass' OR Outcome = 'Fail')
            )
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)

        return todo

    def set_roi_stats(self, project_id, code, md, fa, ga, rd, ad):
        sql = r"""
        INSERT INTO pijp_dti (Code, ProjectID, FileName, Measure, Roi, MinVal, MaxVal, MeanVal, StdDev, MedianVal, 
                              Volume, RecordDate)
        VALUES ({code}, {project_id}, {fname}, {measure}, {roi}, {min}, {max}, {mean}, {sd}, {median}, {vol}, {time})
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
                        sd = fsp(str(row[4]))
                        median_val = fsp(str(row[5]))
                        volume = fsp(str(row[6]))
                        time = fsp(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                        formatted_sql = sql.format(code=fsp(code), project_id=project_id, fname=fname, measure=msr,
                                                   roi=roi, min=min_val, max=max_val, mean=mean_val, sd=sd,
                                                   median=median_val, vol=volume, time=time)
                        self.connection.execute_non_query(formatted_sql)

    def remove_roi_stats(self, project, code):
        project_id = self.get_project_id(project)
        sql = r"""
        DELETE FROM pijp_dti WHERE ProjectID = {project_id} AND Code = {code} 
        """.format(project_id=project_id['ProjectID'], code=fsp(code))

        self.connection.execute_non_query(sql)

    def find_where_left_off(self, project, step):

        sql = r"""
        SELECT ScanCode as Code, Outcome, Comments
        FROM ProcessingLog
        WHERE Project = {project}
        AND Process = {process}
        AND Step = {step} 
        AND CompletedBy = {user} 
        ORDER BY CompletedOn DESC
        """.format(project=fsp(project), step=fsp(step),
                   process=fsp(PROCESS_TITLE), user=fsp(getpass.getuser()))

        left_off = self.connection.fetchone(sql)
        return left_off

    def get_t1(self, project, code):
        in_code = code.split('-')
        subject_code = '-'.join(in_code[0:4])
        sql = r"""
        SELECT
            Code
        FROM ImageList.{project}
        WHERE ScanCode = {code}
            AND ImageType='T1'
        """.format(project=project, code=fsp(subject_code))

        todo = self.connection.fetchone(sql)
        if todo is not None:
            todo = todo["Code"]
        return todo

    def get_finished_nnicv(self, project):

        sql = r"""
        SELECT
            ScanCode AS Code
        FROM 
            ProcessingLog
        WHERE Project = {project}
            AND Process = 'NNICV'
            AND Step = 'QC'
            AND (Outcome = 'Edit' OR Outcome = 'Pass' OR Outcome = 'Fail')
        """.format(project=fsp(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_nnicv_status(self, project, code):

        sql = r"""
        SELECT
            Outcome, CompletedOn
        FROM ProcessingLog
        WHERE Project = {project}
            AND Process = 'NNICV'
            AND Step = 'QC'
            AND ScanCode = {code}  
            AND NOT (
                Outcome = 'Cancelled' 
                OR Outcome = 'Queued' 
                OR Outcome = 'Initiated'
                OR Outcome = 'None')
        ORDER BY CompletedOn DESC
                  
        """.format(project=fsp(project), code=fsp(code))

        status = self.connection.fetchone(sql)
        if status:
            status = status["Outcome"]
        elif status is None:
            status = 'No NNICV result found'
        return status

    def get_mask_status(self, project, code):

        sql = r"""
        SELECT
            Comments
        FROM ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'Mask'
            AND ScanCode = {code}      
        ORDER BY
            CompletedOn DESC      
        """.format(
            project=fsp(project), process=fsp(PROCESS_TITLE), code=fsp(code))

        todo = self.connection.fetchone(sql)

        if todo is not None:
            status = todo["Comments"]
        else:
            status = ""

        return status

    def get_unfinished_nnicv(self, project):

        sql = r"""
        SELECT 
            ScanCode AS Code
        FROM 
            ProcessingLog 
        WHERE Project = {project}
            AND Process = 'NNICV' 
            AND Step = 'NeuralNet' 
            AND Outcome = 'Done' 
            AND ScanCode NOT IN 
                (SELECT DISTINCT ScanCode 
                    FROM ProcessingLog 
                    WHERE Process = 'NNICV' 
                    AND Step = 'QC'
                    AND (Outcome = 'Pass' OR Outcome = 'Edit' OR Outcome = 
                    'Fail')
                )
        """.format(project=fsp(project))

        todo = self.connection.fetchall(sql)
        return todo

    def get_finished_mask_qc(self, project):

        sql = r"""
        SELECT
            ScanCode AS Code
        FROM
            ProcessingLog
        WHERE Project = {project}
            AND Process = {process}
            AND Step = 'MaskQC'
            AND (Outcome = 'Edit' OR Outcome = 'Pass' Or Outcome = 'Fail')
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_staged_nnicv(self, project):

        sql = r"""
        SELECT
            ScanCode AS Code
        FROM
            ProcessingLog
        WHERE
            Project = {project}
            AND Process = {process}
            AND Step = 'Mask'
            AND (Comments = 'Used NNICV final mask.' OR
                 Comments = 'Found failed NNICV mask. Used Otsu mask.')
            AND (Outcome = 'Done')
          
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def get_failed_mask(self, project):

        sql = r"""
        SELECT
            ScanCode AS Code
        FROM
            ProcessingLog
        WHERE
            Project = {project}
            AND Process = {process}
            AND Step = 'Mask'
            AND Outcome = 'Error'
          
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE))

        todo = self.connection.fetchall(sql)
        return todo

    def check_seg_qc_pass(self, project, code):

        sql = r"""
        SELECT
            ScanCode AS Code, Outcome, CompletedOn
        FROM
            ProcessingLog
        WHERE
            Project = {project}
        AND 
            Process = {process}
        AND
            ScanCode = {code}
        AND Step = 'SegQC'
        AND (Outcome = 'Pass' OR Outcome = 'Fail' OR Outcome = 'Error')
        ORDER BY CompletedOn DESC
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE),
                   code=fsp(code))
        todo = self.connection.fetchone(sql)
        if todo:
            todo = todo["Outcome"]
        else:
            todo = ''
        return todo

    def check_warp_qc_pass(self, project, code):

        sql = r"""
        SELECT
            ScanCode AS Code, Outcome, CompletedOn
        FROM
            ProcessingLog
        WHERE
            Project = {project}
        AND 
            Process = {process}
        AND
            ScanCode = {code}
        AND Step = 'WarpQC'
        AND (Outcome = 'Pass' OR Outcome = 'Fail' OR Outcome = 'Error')
        ORDER BY CompletedOn DESC
        """.format(project=fsp(project), process=fsp(PROCESS_TITLE),
                   code=fsp(code))
        todo = self.connection.fetchone(sql)
        if todo:
            todo = todo["Outcome"]
        else:
            todo = ''
        return todo
