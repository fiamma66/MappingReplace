import pandas as pd
import pathlib
import log

__all__ = ['pd', 'MappingExcel', 'pathlib']

logger = log.getLogger(__name__)
logger.addHandler(log.queue_handler)


class MappingExcel:

    def __init__(self, excel, skip_rows, sheetname=None):
        self.format_dict = None
        self.excel = excel
        # logger.info(self.mapping_file_entry)
        self.sheetname = sheetname
        self.skip_rows = skip_rows

        self._csv_or_excel()

        # nan must be empty

        self.excel.dropna(how='all', inplace=True)
        self.excel.fillna('', inplace=True)
        logger.info('Mapping Condition Amount : {}'.format(self.excel.shape[0]))
        self.format_mapping_dict()

    def _csv_or_excel(self):
        """

        :return: Change self.mapping_file_entry to Pandas Object
        """
        logger.info('Reading Mapping File Path !')
        p = pathlib.Path(self.excel).expanduser().resolve()
        if not p.exists():
            raise RuntimeError('File Not Exists !')
        # logger.info(p)
        if p.suffix == '.csv':
            logger.info('Detect CSV File')
            self.excel = pd.read_csv(p)

        elif p.suffix == '.xlsx' or p.suffix == '.xls':
            logger.info('Detect Excel File')
            if self.sheetname is None:
                logger.error('Excel File Detect ! Must Fill SheetName ')
                raise RuntimeError
            if not isinstance(self.skip_rows, int):
                self.skip_rows = int(self.skip_rows)
            self.excel = pd.read_excel(p, sheet_name=self.sheetname, skiprows=self.skip_rows)

    def format_mapping_dict(self):
        """

        :return: Mapping Use Dictionary
        """
        empty_li = []
        col = self.check_col(self.excel.columns)
        col2 = [item for item in self.excel.columns if item not in col]
        ori_list = self.excel[col].values.tolist()
        new_list = self.excel[col2].values.tolist()
        logger.warning('ORI_MAPPING : {}'.format(ori_list))
        logger.warning('NEW_MAPPING : {}'.format(new_list))

        if not len(ori_list) == len(new_list):
            logger.error('Mapping Excel Columns Amount not Match')
            raise RuntimeError

        for i in range(len(ori_list)):
            # List Of Tuple
            empty_li.append((ori_list[i], new_list[i]))

        self.format_dict = empty_li

    def get_format_dict(self) -> list:
        return self.format_dict

    @staticmethod
    def check_col(cols) -> list:
        li = []

        for col in cols:
            if col.upper().startswith('ORI') or col.upper().startswith('ORI_'):
                li.append(col)

        return li


if __name__ == '__main__':
    pass
