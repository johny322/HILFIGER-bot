from pydantic import BaseModel


class LogModel(BaseModel):
    photo: bool = True
    title: bool = True
    price: bool = True
    location: bool = True
    description: bool = False
    views: bool = False
    created: bool = False
    seller_name: bool = True
    seller_rate: bool = False
    posts_count: bool = True
    seller_reg: bool = True
    only_with_phone: bool = True
    check_wa: bool = True


def decode_log_config(config: str) -> LogModel:
    cfg_list = config.split("_")[1:]
    log_fields = list(LogModel.__fields__)
    key_args = {}
    for i in range(len(config.split("_")) - 1):
        key_args[log_fields[i]] = bool(int(cfg_list[i]))

    return LogModel(**key_args)


def encode_log_config(log: LogModel) -> str:
    return "cfg_" + "_".join(map(lambda v: str(int(v)), log.dict().values()))
