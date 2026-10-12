import numpy as np
from pathlib import Path

import soundfile as sf

class AudioProcessing:
    @classmethod
    def norm_loudness(cls, 
                      paths: list[str]
                      ) -> list:
        rms_list = {}
            
        for path in paths:
            if Path(path).suffix != ".wav":
                continue
            data, rate = sf.read(path)
            if data.ndim > 1:
                data = np.mean(data, axis=1)
            rms = np.sqrt(np.mean(data**2))
            rms_list[path] = rms
            
        min_rms = min(rms_list.values())
        
        coe_dict = {}
        for path, rms in rms_list.items():
            if rms == 0:
                coe_dict[path] = 1.0
                continue
            coe = min_rms / rms
            coe_dict[path] = float(coe)
            
        return coe_dict
