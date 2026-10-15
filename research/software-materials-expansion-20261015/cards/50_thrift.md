# 50_thrift — IDL 多文件语义前端与反射输出恢复
- 来源：[apache/thrift](https://github.com/apache/thrift)；SHA `f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe`；M2 / `build_scope_probe`。
- 已有：上游已有 lexer/parser、include、AST/type/constant/service 与多语言生成器。恢复题的缺失来自拟定掩码，尚未实施，不是上游功能缺陷。
- 拟任务缺口：拟保留构建/CLI/lexer/语法框架，联合移除 include绑定、类型/常量语义与结构/service反射生成的一组实现；边界需先证明仍可构建且共享语义连通。
- 产品/子系统边界：恢复可用的 IDL→语义模型→JSON反射与固定Python生成路径：跨include的typedef/enum/容器常量、service继承/异常与字段requiredness一致；不要求重写所有语言runtime。
## 模块链与固定证据
- [`compiler/cpp/src/thrift/thrifty.yy:324`](https://github.com/apache/thrift/blob/f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe/compiler/cpp/src/thrift/thrifty.yy#L324)：include在独立解析阶段加入program图
- [`compiler/cpp/src/thrift/parse/t_program.h:44`](https://github.com/apache/thrift/blob/f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe/compiler/cpp/src/thrift/parse/t_program.h#L44)：program汇集typedef/const/struct/service及include作用域
- [`compiler/cpp/src/thrift/generate/t_json_generator.cc:599`](https://github.com/apache/thrift/blob/f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe/compiler/cpp/src/thrift/generate/t_json_generator.cc#L599)：反射生成字段、union/exception及service语义
- [`compiler/cpp/tests/cpp/t_cpp_parser_string_constant_tests.cc:37`](https://github.com/apache/thrift/blob/f4d8e8c3fa56ef04d7462e26d3b8226127edb2fe/compiler/cpp/tests/cpp/t_cpp_parser_string_constant_tests.cc#L37)：真实解析测试检查AST常量及lexer错误信息
## 组合场景
1. 三个include文件定义enum→typedef→嵌套容器常量，CLI反射与生成Python读取同一值。
2. 子service继承父service，方法使用跨文件struct和声明异常，生成代码导入/调用/序列化契约一致。
3. 非法重定义、错误类型default和转义字符串跨文件出现，报告正确文件/位置，合法相邻定义仍正常生成。
## 基线与退出
- 强合法基线：保留未掩码AST/低层runtime，正常利用现成parser和序列化库；现成thrift CLI/JSON生成器作为首个包装基线，若可直接替代全部交付则不把任务称恢复难题。
- 首探/退出：先定义可构建掩码并跑最小跨include IDL；试用现成parser/包装器，测是否仅少量adapter即可恢复全部规格。若是则hold；不得靠引入非标准语法加难。
- 早期完成后的剩余假设：单文件struct成功后，include命名空间、typedef链、容器常量/default与service继承共享身份仍可能未恢复。
- 早期完成后的剩余假设：生成文本正确后，真实Python构造/读写、错误定位、重复生成稳定与字段/异常兼容仍需端到端验证。
- 独立 oracle / 原生回归：固定上游compiler离线oracle对照规范化JSON/诊断，独立Python构造序列化与手工golden；保留parser/native compiler test及ThriftTest规格；oracle不可见不等于评分只隐藏文本。
- 许可观察：根 LICENSE Apache-2.0，NOTICE已保存；语言runtime与生成器附带notice需打包时保留。
- 离线/架构风险：预装C++/CMake、flex/bison与目标Python runtime；只选固定语言后端避免全生态依赖，生成源和跨CPU ABI需分别校验。
- 官方在线核对：[primary](https://github.com/apache/thrift)；[primary](https://thrift.apache.org/docs/idl)
- 仅完成定向源码/测试阅读，未构造完整题包或运行；task_constructed=false；runtime_verified=false；six_hour_difficulty_verified=false。
