# 外部参考样例说明

本目录用于存放来自外部专业软件的对标样例，例如：

- JHora
- Maitreya
- 其他可验证的 Jyotish 软件

## 文件格式

- 一个样例对应一个 `*.json`
- 推荐文件名与 `tests/regression/fixtures/` 中的内部样例保持一致

## 生成模板

```bash
PYTHONPATH=src .venv/bin/python scripts/create_external_reference_template.py shanghai_lahiri
```

## 填写原则

- 必须保持 `birth_data` 和 `profile` 不变
- `expected` 值来自外部软件，不要填当前项目的输出
- 若外部软件使用了不同默认项，必须先在本项目中对齐参数口径

## 运行测试

```bash
.venv/bin/python -m pytest tests/reference
```

未填写完的模板会被自动 `skip`，不会让测试失败。
