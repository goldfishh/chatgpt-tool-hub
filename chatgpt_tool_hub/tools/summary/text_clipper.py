from typing import List

from ...models.calculate_token import count_string_tokens as get_token_num


class TextClipper:
    def __init__(self, max_segment_length=2500, seperator="\n"):
        self.max_segment_length = max_segment_length
        self.seperator = seperator

    def _clip_single_long_text(self, text: str) -> List[str]:
        _token_num = get_token_num(text)
        if _token_num <= self.max_segment_length:
            return [text]

        _cut_step = min(int(len(text) * self.max_segment_length / _token_num), self.max_segment_length)
        _cut_index = list(range(0, len(text), _cut_step))
        # add index to stop
        _cut_index.append(len(text))

        _iter = 0
        clip_list = []
        while _iter < len(_cut_index) - 1:
            # todo: some words or sentences may be split in two parts
            _clip_text = text[_cut_index[_iter]:_cut_index[_iter + 1]]
            _cut_token_num = get_token_num(_clip_text)
            if _cut_token_num <= self.max_segment_length:
                clip_list.append(_clip_text)
            _iter += 1
        return clip_list

    def clip(self, text: str, capacity: int = 0) -> List[str]:
        if get_token_num(text) <= self.max_segment_length:
            return [text]
        capacity = max(capacity, 0)
        segments = text.split(self.seperator)
        segments = list(filter(lambda x: x.strip() != "", segments))
        _segment_num = len(segments)

        clip_list = []
        segment_cache = ""

        now_ctn, total_ctn = 0, 0
        for iter in range(_segment_num):
            _mix_text = self.seperator.join([segment_cache, segments[iter]])
            _token_num_of_mix = get_token_num(_mix_text)
            if _token_num_of_mix > self.max_segment_length:
                # 长文本
                if now_ctn == 1:
                    clip_list.extend(self._clip_single_long_text(segment_cache))
                elif now_ctn > 1:
                    clip_list.append(segment_cache)
                total_ctn += now_ctn
                # not precise here
                if capacity != 0 and total_ctn >= capacity:
                    # early stop
                    segment_cache = ""
                    break
                segment_cache = segments[iter]
                now_ctn = 1
            else:
                segment_cache = _mix_text
                now_ctn += 1
        if segment_cache:
            clip_list.extend(self._clip_single_long_text(segment_cache))
        return clip_list