# import traceback
import log
from mapping import *
import progressbar
import re
import time
# import sys


progressbar.streams.wrap_stderr()
logger = log.getLogger(__name__)
logger.addHandler(log.queue_handler)


class SafeDict(dict):
    def __missing__(self, key):
        return '{' + key + '}'


def file_len(fname):
    try:
        with open(fname, 'r', encoding='UTF-8') as f:
            for i, l in enumerate(f):
                pass
    except UnicodeDecodeError:
        try:
            with open(fname, 'r', encoding='big5') as f:
                for i, l in enumerate(f):
                    pass
        except ValueError:
            return 0
    return i + 1


class MyProcess:

    def __init__(self, mapping_file, target_file, output_path, skip_rows, sheetname=None, p_bar=None):
        mapping = MappingExcel(excel=mapping_file, sheetname=sheetname, skip_rows=skip_rows)
        self.mapping = mapping.get_format_dict()
        self.target_file = target_file
        self.prepare_target_file()
        self.log_list = []
        self.log_file = None
        # GUI Progressbar

        self.p_bar = p_bar
        self.p_value = 0

        # progressbar2 Bar
        self.progressbar = None

        self.output = pathlib.Path(output_path).expanduser().resolve()
        if not self.output.exists():
            self.output.mkdir(parents=True, exist_ok=True)

        self.regex_check = re.compile(r'\br\b ', flags=re.I)

    def prepare_target_file(self):
        if isinstance(self.target_file, list):
            # logger.warning('list')
            # logger.warning(self.target_file)
            self.target_file = [pathlib.Path(f).expanduser().resolve() for f in self.target_file
                                if pathlib.Path(f).is_file()]
        else:
            logger.error('Parsing List Fail')
            raise RuntimeError

    def run(self):

        total_len = sum([file_len(file) * len(self.mapping) for file in self.target_file])
        # self.progressbar = progressbar.ProgressBar().start(max_value=total_len)
        logger.info('Total Reading Lines (Include Mapping Loop) : {}'.format(total_len))
        self.p_bar['maximum'] = total_len

        for index, file in enumerate(self.target_file):
            logger.info('Now Processing : {}'.format(file.name))

            try:
                with open(file, 'r', encoding='UTF-8') as f:
                    lines = f.readlines()
                encoder = 'UTF-8'
            except UnicodeDecodeError:
                logger.warning('UTF-8 Decode Fail ! Trying Big5 !!')
                try:
                    with open(file, 'r', encoding='BIG5') as f:
                        lines = f.readlines()
                    encoder = 'BIG5'
                except ValueError:
                    logger.warning('Neither "UTF-8" Nor "Big5" Can Decode File ! '
                                   'File May Be Binary File !! IGNORED IT !! '
                                   'Check It Manually   File : {}'.format(file))
                    continue

            for dic in self.mapping:
                # logger.info('Looping in Condition Rows')
                # logger.info('From {} to {}'.format(*dic))
                lines = [self.replace_string(line, dic, file.name, i) for i, line in enumerate(lines)]
                self.p_bar['value'] = self.p_value

            with open(file, 'w', encoding=encoder) as f:
                f.writelines(lines)
            # else:
            #     with open(file, 'wb') as f:
            #         f.writelines([line.encode('big5') for line in lines])

            # logger.info('File += 1 '
            #             'Now : {}'.format(self.p_value))
            self.p_bar['value'] = self.p_value
            # self.progressbar.update(self.p_value)
            # self.progressbar.update(self.p_value)

        logger.info('Log Amount : {}'.format(len(self.log_list)))
        # self.progressbar.finish()
        if len(self.log_list) != 0:
            self.log_file = pd.DataFrame(self.log_list, columns=[
                'FileName', 'Modified Line', 'Ori_Value1', 'New_Value1',
                'Ori_Value2', 'New_Value2', 'Ori_Value3', 'New_Value3',
                'Ori_Value4', 'New_Value4', 'Ori_Value5', 'New_Value5'
            ])
            self.log_file.sort_values(['FileName', 'Modified Line'], inplace=True)
            output_file = self.output / './Modified_Summary_{}.xlsx'.format(time.strftime('%Y%m%d%H%M%S'))
            logger.info('Writting Summary to {}'.format(output_file))
            self.log_file.to_excel(output_file, index=False)

    def __rex_use(self, old_mapping, new_mapping):
        """
        :param old_mapping: Excel old Mapping
        :return: 1. if there is regex {r REGEX} in old Mapping
                 Split it and update old Mapping

                 2. if use_regex is true , replace all $1 $2 in new Mapping
        """

        use_regex = False
        # logger.warning('Passing Mapping is '.format(old_mapping))
        prepare_old_mapping = ()

        for i, mapping in enumerate(old_mapping):

            if re.search(self.regex_check, str(mapping)):
                # logger.warning('Detecting Regex Mapping')
                use_regex = True

                # logger.warning('Splitting Regex Mapping')

                sp = re.split(pattern=self.regex_check, string=mapping)

                # logger.error(sp)

                prepare_old_mapping = prepare_old_mapping + (re.compile(sp[1], flags=re.I), )
                # logger.warning('Complete Splitting Regex')
                # logger.warning(old_mapping[i])
            else:
                prepare_old_mapping = prepare_old_mapping + (mapping, )

        if use_regex:

            # logger.warning('Change $NUM to {V_PRE$NUM}')

            new_mapping = [re.sub(r'\$(\d+)', r'{V_PRE\g<1>}', mapping) for mapping in new_mapping]

        return prepare_old_mapping, new_mapping, use_regex

    def replace_string(self, string, mapping_tuple, filename, line_num):
        old = mapping_tuple[0]
        new = mapping_tuple[1]
        self.p_value += 1
        # self.progressbar.update(self.p_value)
        string = string.upper()
        # logger.warning('Old : {}'.format(old))
        _old, _new, use_regex = self.__rex_use(old, new)

        # logger.error('New And Last : {}'.format(_old))

        # logger.warning('Origin from class : {}'.format(self.mapping))

        # format dict to replace
        map_dict = dict(zip(_old, _new))

        li = [filename]

        if not use_regex:
            if all(ele.upper() in string for ele in _old):
                li.append(line_num + 1)
                for key, item in map_dict.items():
                    li.extend([key, item])
                    # string = string.replace(key, item)
                    string = re.sub(key, item, string, flags=re.I)
                if len(li) < 12:
                    li.extend([''] * (12 - len(li)))
                # logger.error(li)
                self.log_list.append(li)
            return string

        else:
            # Use Regex is True
            # logger.warning('Entering Regex Replacing')
            # logger.warning(old)
            # logger.warning(string)
            if all(self.loop_checking(ele, string) for ele in _old):
                # logger.error('All 條件符合')
                li.append(line_num + 1)

                for key, item in map_dict.items():

                    searching = re.search(key, string)
                    dict_to_format = {}
                    for i in range(len(searching.groups())):
                        _keys = 'V_PRE{}'.format(i + 1)
                        dict_to_format[_keys] = searching.group(i + 1)

                    string = re.sub(key, item.format_map(SafeDict(dict_to_format)), string)
                    li.extend([searching.group(), item.format_map(SafeDict(dict_to_format))])

                if len(li) < 12:
                    li.extend([''] * (12 - len(li)))
                # logger.error(li)
                self.log_list.append(li)
            return string

    @staticmethod
    def loop_checking(ele, string):
        # logger.warning(ele)
        # logger.error('{} : {}'.format(ele, string))

        if isinstance(ele, str):
            # logger.warning('ele is string')
            return ele.upper() in string

        else:
            if re.search(ele, string):
                return True


def main(mapping_file, target, skip_rows, sheetname=None, output_path=None, button=None, p_bar=None):

    if button is not None:
        button.config(state='disable')
    try:
        p = MyProcess(mapping_file=mapping_file, target_file=target,
                      sheetname=sheetname, output_path=output_path,
                      skip_rows=skip_rows, p_bar=p_bar)
        p.run()
    except Exception as e:
        # print(e)
        logger.error(e)

    logger.info('Processing End !')
    if button is not None:
        button.config(state='normal')


def __add_option(parser):
    parser.add_argument('--no-gui', dest='gui',
                        action='store_true',
                        help='Open GUI to Import Job')


if __name__ == '__main__':
    pass
