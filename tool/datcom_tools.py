from langchain_core.tools import tool
from typing import Dict, Any, Optional, List, Union
from pydantic import BaseModel, Field, ValidationError
import json

# Import our DATCOM models
try:
    from .datcom_models import (
        DatcomInputModel, FltconModel, SynthsModel, OptinsModel, 
        BodyModel, WgplnfModel, HtplnfModel, VtplnfModel, TerminationCommands
    )
except ImportError:
    from tool.datcom_models import (
        DatcomInputModel, FltconModel, SynthsModel, OptinsModel, 
        BodyModel, WgplnfModel, HtplnfModel, VtplnfModel, TerminationCommands
    )

class DatcomValidationResult(BaseModel):
    """DATCOM 格式驗證結果"""
    is_valid: bool = Field(description="是否通過驗證")
    errors: List[str] = Field(default=[], description="驗證錯誤列表")
    warnings: List[str] = Field(default=[], description="驗證警告列表")
    validated_data: Optional[Dict[str, Any]] = Field(default=None, description="驗證通過的數據")
    summary: Optional[Dict[str, Any]] = Field(default=None, description="驗證摘要信息")

@tool
def validate_datcom_format(datcom_content: str) -> DatcomValidationResult:
    """
    驗證 DATCOM 輸入檔案格式。
    
    Args:
        datcom_content: DATCOM 輸入檔案內容（JSON 格式或原始文本）
        
    Returns:
        DatcomValidationResult: 包含驗證結果、錯誤和警告的結構化數據
    """
    result = DatcomValidationResult(is_valid=False)
    
    try:
        # 嘗試解析為 JSON
        if datcom_content.strip().startswith('{'):
            datcom_data = json.loads(datcom_content)
            return _validate_json_datcom(datcom_data, result)
        else:
            # 如果是原始文本，進行基本格式檢查
            result.warnings.append("檢測到原始文本格式，建議使用結構化 JSON 格式")
            return _validate_raw_datcom_text(datcom_content, result)
            
    except json.JSONDecodeError as e:
        result.errors.append(f"JSON 解析錯誤: {str(e)}")
        return result
    except Exception as e:
        result.errors.append(f"未預期的錯誤: {str(e)}")
        return result

def _validate_json_datcom(datcom_data: Dict[str, Any], result: DatcomValidationResult) -> DatcomValidationResult:
    """驗證 JSON 格式的 DATCOM 數據"""
    try:
        # 使用 Pydantic 模型驗證
        validated_model = DatcomInputModel(**datcom_data)
        
        result.is_valid = True
        result.validated_data = validated_model.model_dump()
        result.warnings.append("DATCOM 格式驗證通過")
        
        # 生成驗證摘要
        result.summary = _generate_validation_summary(validated_model)
        
        # 額外的邏輯檢查
        _perform_logic_checks(validated_model, result)
        
    except ValidationError as e:
        result.errors.extend([f"欄位驗證錯誤: {'.'.join(str(loc) for loc in error['loc'])} - {error['msg']}" for error in e.errors()])
    except Exception as e:
        result.errors.append(f"模型驗證錯誤: {str(e)}")
    
    return result

def _validate_raw_datcom_text(content: str, result: DatcomValidationResult) -> DatcomValidationResult:
    """驗證原始 DATCOM 文本格式"""
    result.is_valid = True
    
    # 基本格式檢查
    required_sections = ['$FLTCON', '$SYNTHS', '$OPTINS']
    optional_sections = ['$BODY', '$WGPLNF', '$HTPLNF', '$VTPLNF']
    missing_required = []
    found_optional = []
    
    for section in required_sections:
        if section not in content:
            missing_required.append(section)
    
    for section in optional_sections:
        if section in content:
            found_optional.append(section)
    
    if missing_required:
        result.errors.extend([f"缺少必要區段: {section}" for section in missing_required])
        result.is_valid = False
    
    # 檢查基本語法
    if '$END' not in content:
        result.warnings.append("建議加入 $END 終止標記")
    
    if 'NEXT CASE' not in content:
        result.warnings.append("建議加入 NEXT CASE 指令")
    
    if result.is_valid:
        result.summary = {
            "format": "raw_text",
            "required_sections": len(required_sections) - len(missing_required),
            "optional_sections": len(found_optional),
            "total_sections": len(required_sections) - len(missing_required) + len(found_optional)
        }
    
    return result

def _generate_validation_summary(model: DatcomInputModel) -> Dict[str, Any]:
    """生成驗證摘要信息"""
    summary = {
        "case_id": model.case_id,
        "units": model.units,
        "flight_conditions": {
            "mach_count": model.fltcon.NMACH,
            "alpha_count": model.fltcon.NALPHA,
            "altitude_count": model.fltcon.NALT if hasattr(model.fltcon, 'NALT') else 0,
        },
        "components": {
            "body": model.body is not None,
            "wing": model.wgplnf is not None,
            "horizontal_tail": model.htplnf is not None,
            "vertical_tail": model.vtplnf is not None,
        },
        "airfoils": {
            "wing_airfoil": model.wing_airfoil is not None,
            "ht_airfoil": model.ht_airfoil is not None,
            "vt_airfoil": model.vt_airfoil is not None,
        }
    }
    return summary

def _perform_logic_checks(model: DatcomInputModel, result: DatcomValidationResult):
    """執行邏輯一致性檢查"""
    
    # 檢查馬赫數數量與列表長度一致性
    if model.fltcon.NMACH != len(model.fltcon.MACH):
        result.warnings.append(f"NMACH ({model.fltcon.NMACH}) 與 MACH 列表長度 ({len(model.fltcon.MACH)}) 不一致")
    
    # 檢查攻角數量與列表長度一致性
    if model.fltcon.NALPHA != len(model.fltcon.ALSCHD):
        result.warnings.append(f"NALPHA ({model.fltcon.NALPHA}) 與 ALSCHD 列表長度 ({len(model.fltcon.ALSCHD)}) 不一致")
    
    # 檢查高度設置
    if hasattr(model.fltcon, 'NALT') and hasattr(model.fltcon, 'ALT'):
        if model.fltcon.NALT != len(model.fltcon.ALT):
            result.warnings.append(f"NALT ({model.fltcon.NALT}) 與 ALT 列表長度 ({len(model.fltcon.ALT)}) 不一致")
    
    # 檢查機身點數與座標列表長度
    if model.body and model.body.NX:
        if len(model.body.X) != model.body.NX:
            result.warnings.append(f"機身點數 NX ({model.body.NX}) 與 X 座標列表長度 ({len(model.body.X)}) 不一致")
        
        # 檢查橫截面定義的一致性
        if model.body.R and len(model.body.R) != model.body.NX:
            result.warnings.append(f"機身點數 NX ({model.body.NX}) 與 R 列表長度 ({len(model.body.R)}) 不一致")
        elif model.body.S and len(model.body.S) != model.body.NX:
            result.warnings.append(f"機身點數 NX ({model.body.NX}) 與 S 列表長度 ({len(model.body.S)}) 不一致")
    
    # 檢查 LOOP 參數有效性
    if model.fltcon.LOOP and model.fltcon.LOOP not in [1.0, 2.0, 3.0]:
        result.warnings.append(f"LOOP 參數 ({model.fltcon.LOOP}) 不在建議值範圍內 [1.0, 2.0, 3.0]")

@tool  
def create_datcom_template(case_id: str, aircraft_type: str = "generic") -> Dict[str, Any]:
    """
    創建 DATCOM 輸入檔案模板。
    
    Args:
        case_id: 案例識別符
        aircraft_type: 飛機類型 ("fighter", "transport", "generic")
        
    Returns:
        Dict[str, Any]: DATCOM 輸入檔案模板
    """
    
    # 根據飛機類型提供不同的預設值
    if aircraft_type == "fighter":
        template_data = _create_fighter_template(case_id)
    elif aircraft_type == "transport":
        template_data = _create_transport_template(case_id)
    else:
        template_data = _create_generic_template(case_id)
    
    return template_data

def _create_generic_template(case_id: str) -> Dict[str, Any]:
    """創建通用飛機模板"""
    return {
        "case_id": case_id,
        "units": "FT",
        "fltcon": {
            "NMACH": 3.0,
            "MACH": [0.3, 0.6, 0.9],
            "NALT": 2.0,
            "ALT": [0.0, 10000.0],
            "NALPHA": 5.0,
            "ALSCHD": [0.0, 5.0, 10.0, 15.0, 20.0],
            "LOOP": 1.0
        },
        "synths": {
            "XCG": 1.0,
            "ZCG": 0.0,
            "XW": 0.8,
            "ZW": 0.0,
            "ALIW": 0.0,
            "XH": 2.5,
            "ZH": 0.2,
            "ALIH": 0.0,
            "XV": 2.3,
            "ZV": 0.0
        },
        "optins": {
            "SREF": 10.0,
            "CBARR": 1.0,
            "BLREF": 8.0
        },
        "body": {
            "NX": 5,
            "X": [0.0, 0.5, 1.0, 1.5, 2.0],
            "R": [0.0, 0.3, 0.4, 0.3, 0.0]
        },
        "wgplnf": {
            "CHRDR": 1.2,
            "CHRDTP": 0.6,
            "SSPN": 4.0,
            "SSPNE": 3.8,
            "SAVSI": 30.0,
            "CHSTAT": 0.25,
            "TWISTA": 0.0,
            "TYPE": 1.0
        }
    }

def _create_fighter_template(case_id: str) -> Dict[str, Any]:
    """創建戰鬥機模板"""
    template = _create_generic_template(case_id)
    # 戰鬥機特定修改
    template["fltcon"]["MACH"] = [0.5, 0.9, 1.2, 1.5, 2.0]
    template["fltcon"]["NMACH"] = 5.0
    template["wgplnf"]["SAVSI"] = 45.0  # 更大的後掠角
    return template

def _create_transport_template(case_id: str) -> Dict[str, Any]:
    """創建運輸機模板"""
    template = _create_generic_template(case_id)
    # 運輸機特定修改
    template["fltcon"]["MACH"] = [0.2, 0.4, 0.6, 0.8]
    template["fltcon"]["NMACH"] = 4.0
    template["wgplnf"]["SAVSI"] = 25.0  # 較小的後掠角
    template["optins"]["SREF"] = 50.0  # 更大的參考面積
    return template

@tool
def send_datcom_to_subgraph(validated_datcom: Dict[str, Any], target_node: str = "datcom_verification_node") -> Dict[str, Any]:
    """
    將已驗證的 DATCOM 數據發送到指定的子圖節點進行進一步處理。
    
    Args:
        validated_datcom: 已經通過驗證的 DATCOM 數據
        target_node: 目標子圖節點名稱
        
    Returns:
        Dict[str, Any]: 準備發送到子圖的處理結果
    """
    
    # 準備發送到子圖節點的數據包
    subgraph_payload = {
        "action": "datcom_verification",
        "timestamp": "2025-10-07",  # 可以用實際時間戳
        "source": "datcom_tools",
        "target_node": target_node,
        "data": {
            "validated_datcom": validated_datcom,
            "metadata": {
                "case_id": validated_datcom.get("case_id", "unknown"),
                "units": validated_datcom.get("units", "FT"),
                "components_count": len([k for k in validated_datcom.keys() if k not in ["case_id", "units", "termination"]]),
                "validation_status": "passed"
            }
        },
        "processing_instructions": {
            "verify_aerodynamic_consistency": True,
            "check_physical_constraints": True,
            "validate_computational_requirements": True
        }
    }
    
    result = {
        "status": "success",
        "message": f"DATCOM 數據已準備發送到子圖節點: {target_node}",
        "payload": subgraph_payload,
        "next_action": "ready_for_subgraph_execution",
        "summary": {
            "case_id": validated_datcom.get("case_id", "unknown"),
            "target_node": target_node,
            "data_size": len(str(validated_datcom)),
            "components": list(validated_datcom.keys())
        }
    }
    
    return result

@tool
def check_datcom_completeness(datcom_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    檢查 DATCOM 數據的完整性和必要組件。
    
    Args:
        datcom_data: DATCOM 數據字典
        
    Returns:
        Dict[str, Any]: 完整性檢查結果
    """
    
    required_components = ["fltcon", "synths", "optins"]
    optional_components = ["body", "wgplnf", "htplnf", "vtplnf"]
    
    missing_required = [comp for comp in required_components if comp not in datcom_data]
    present_optional = [comp for comp in optional_components if comp in datcom_data]
    
    completeness_score = (len(required_components) - len(missing_required)) / len(required_components)
    if present_optional:
        # 加分為可選組件
        completeness_score += 0.1 * len(present_optional)
    
    completeness_score = min(completeness_score, 1.0)  # 最大為 1.0
    
    result = {
        "completeness_score": round(completeness_score, 2),
        "is_complete": len(missing_required) == 0,
        "missing_required": missing_required,
        "present_optional": present_optional,
        "recommendations": []
    }
    
    if missing_required:
        result["recommendations"].extend([f"需要添加必要組件: {comp}" for comp in missing_required])
    
    if not present_optional:
        result["recommendations"].append("建議至少添加一個幾何組件 (body, wgplnf, htplnf, vtplnf)")
    
    if "wing_airfoil" not in datcom_data and "wgplnf" in datcom_data:
        result["recommendations"].append("建議為機翼添加翼型定義")
    
    return result
