from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator, model_validator

# --- Helper Models ---

class TerminationCommands(BaseModel):
    """定義檔案結尾的指令。"""
    DIM: Literal["FT", "M"] = Field("FT", description="指定輸入尺寸單位")
    BUILD: bool = Field(True, description="顯示所有部件的數據")
    PLOT: bool = Field(True, description="產生 MATLAB 繪圖檔")
    NEXT_CASE: bool = Field(True, description="包含 'NEXT CASE' 終止指令")

# --- Namelist Models ---

class FltconModel(BaseModel):
    """定義飛行條件。"""
    NMACH: float = Field(..., description="要運行的馬赫數數量")
    MACH: List[float] = Field(..., description="馬赫數列表")
    NALT: float = Field(..., description="要運行的高度數量")
    ALT: List[float] = Field(..., description="高度列表 (單位由頂層 units 決定)")
    NALPHA: float = Field(..., description="要運行的攻角數量")
    ALSCHD: List[float] = Field(..., description="攻角排程列表 (單位：度)")
    WT: Optional[float] = Field(None, description="飛行器重量 (單位：磅或牛頓)")
    LOOP: Optional[float] = Field(1.0, description="控制分析的主迴圈結構，有效值為 1.0, 2.0, 3.0")

class SynthsModel(BaseModel):
    """定義各個部件的相對位置。"""
    XCG: float = Field(..., description="重心的 X 座標")
    ZCG: float = Field(..., description="重心的 Z 座標")
    XW: float = Field(..., description="機翼翼尖前緣的 X 座標")
    ZW: float = Field(..., description="機翼翼尖前緣的 Z 座標")
    ALIW: float = Field(..., description="機翼安裝角 (incidence angle)")
    XH: float = Field(..., description="水平尾翼翼尖前緣的 X 座標")
    ZH: float = Field(..., description="水平尾翼翼尖前緣的 Z 座標")
    ALIH: float = Field(..., description="水平尾翼安裝角")
    XV: float = Field(..., description="垂直尾翼翼尖前緣的 X 座標")
    ZV: float = Field(..., description="垂直尾翼翼尖前緣的 Z 座標")

class OptinsModel(BaseModel):
    """定義參考參數。"""
    SREF: float = Field(..., description="參考機翼面積")
    CBARR: Optional[float] = Field(None, description="參考平均氣動力弦長")
    BLREF: Optional[float] = Field(None, description="參考翼展")

class BodyModel(BaseModel):
    """
    **【大幅擴充】** 定義機身幾何外型，支援多種定義方式。
    """
    NX: float = Field(..., description="定義機身的站位數量")
    X: List[float] = Field(..., description="各個站位的 X 座標列表")
    # **【補充】** 允許多種方式定義橫截面，但必須擇一
    S: Optional[List[float]] = Field(None, description="各個站位的橫截面積列表 (用於軸對稱機身)")
    R: Optional[List[float]] = Field(None, description="各個站位的機身半徑列表 (S 的替代方案)")
    ZU: Optional[List[float]] = Field(None, description="各個站位的上表面 Z 座標列表 (用於非圓形機身)")
    ZL: Optional[List[float]] = Field(None, description="各個站位的下表面 Z 座標列表 (用於非圓形機身)")
    # **【補充】** 新增計算方法控制參數
    ITYPE: Optional[float] = Field(None, description="翼身干擾計算標誌")
    METHOD: Optional[float] = Field(None, description="計算方法標誌")

    @model_validator(mode='before')
    @classmethod
    def check_cross_section_definition(cls, values):
        if isinstance(values, dict):
            definitions = [values.get('S'), values.get('R'), values.get('ZU')]
            if sum(d is not None for d in definitions) > 1:
                raise ValueError("只能提供 S, R, 或 (ZU, ZL) 其中一種橫截面定義方式")
            if values.get('ZU') is not None and values.get('ZL') is None:
                raise ValueError("如果提供了 ZU，則必須同時提供 ZL")
        return values

class WgplnfModel(BaseModel):
    """
    定義機翼的平面幾何外型，**【補充】** 了條件驗證。
    """
    CHRDR: float = Field(..., description="翼根弦長")
    CHRDTP: float = Field(..., description="翼尖弦長")
    SSPN: float = Field(..., description="理論半翼展")
    SSPNE: Optional[float] = Field(None, description="暴露的半翼展")
    SAVSI: float = Field(..., description="內側翼板的後掠角")
    CHSTAT: float = Field(0.25, description="後掠角參考的弦長百分比")
    TWISTA: Optional[float] = Field(0.0, description="翼尖扭轉角")
    DHDADI: Optional[float] = Field(None, description="內側翼板的上反角 (dihedral)")
    TYPE: float = Field(1.0, description="翼平面外型類型 (1.0=直線尖削, 2.0=曲折翼)")
    # **【補充】** 僅用於曲折翼 (TYPE=2.0) 的參數
    CHRDBP: Optional[float] = Field(None, description="內外側翼板交接處的弦長")
    SSPNOP: Optional[float] = Field(None, description="外側翼板的半翼展")
    SAVSO: Optional[float] = Field(None, description="外側翼板的後掠角")
    DHDADO: Optional[float] = Field(None, description="外側翼板的上反角")

    @model_validator(mode='before')
    @classmethod
    def check_cranked_wing_params(cls, values):
        if isinstance(values, dict):
            if values.get('TYPE') == 2.0:
                required_params = ['CHRDBP', 'SSPNOP', 'SAVSO']
                if not all(values.get(p) is not None for p in required_params):
                    raise ValueError("對於 TYPE=2.0 (曲折翼)，必須提供 CHRDBP, SSPNOP, SAVSO")
        return values

class HtplnfModel(WgplnfModel):
    """定義水平尾翼的平面幾何外型 (繼承自 WgplnfModel)。"""
    pass

class VtplnfModel(WgplnfModel):
    """定義垂直尾翼的平面幾何外型 (繼承自 WgplnfModel)。"""
    pass

# --- Top-Level Model ---

class DatcomInputModel(BaseModel):
    """
    DATCOM 輸入檔案的頂層資料結構。
    """
    case_id: str = Field(..., description="案例的唯一識別符")
    # **【補充】** 新增全域單位設定
    units: Literal["FT", "M"] = Field("FT", description="專案使用的主要長度單位")
    fltcon: FltconModel
    synths: SynthsModel
    optins: OptinsModel
    body: Optional[BodyModel] = None
    
    wing_airfoil: Optional[str] = Field(None, description="機翼的翼型代號，例如 NACA-W-6-66-012")
    wgplnf: Optional[WgplnfModel] = None
    
    ht_airfoil: Optional[str] = Field(None, description="水平尾翼的翼型代號")
    htplnf: Optional[HtplnfModel] = None
    
    vt_airfoil: Optional[str] = Field(None, description="垂直尾翼的翼型代號")
    vtplnf: Optional[VtplnfModel] = None
    
    termination: Optional[TerminationCommands] = None