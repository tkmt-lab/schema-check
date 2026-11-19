# schema-check：canonical JSON の空性と最短完結の点検

**版 0.1.0 · 公開日 2026-11-20 · DOI：未指定**

著者 滝本竜彦（Tatsuhiko Takimoto） · https://github.com/tkmt-lab/schema-check

JSON Schema を登録する開発者や CI の担当が、構造化出力の制約を点検するための道具です。
対応する canonical UTF-8 参照言語について、空かどうかと接頭辞からの最短の完結を出し、別入口で検査します。
外部の生成ツールとの比較は、固定版に対する有限の入力例での観測です。

Python 3.10 以降と POSIX `ps` を使い、macOS または Linux でこのディレクトリから実行します。

```sh
mkdir -p .cache/examples
python3 -B schema-check examples/object.json --prefix '{"modifier":' -o .cache/examples/result.json
python3 -B schema-check verify .cache/examples/result.json --schema examples/object.json
```

期待する suffix は `""}`（3 byte）。生成時は `verification: NOT_RUN`、別入口の検査は `verification: PASS` です。

## 詳しい説明

[英語 README](README.md) に、数値・空の言語・部分 UTF-8 の例、固定語彙での token 証拠、保存した一式の検査手順があります。[検査の境界](docs/VERIFICATION.md) は、生成器と別入口の検査器が共有する意味論などの核を説明します。

## 範囲

対象は、対応する canonical UTF-8 参照言語と、固定した三つの語彙です。一般の JSON Schema、すべての JSON 表記・語彙、任意 sampling の終了、外部 backend の全言語一致は保証しません。有限の検算と共有核を用いる検査であり、形式証明・人間による独立査読・新規性・性能の優越性は主張しません。詳しい条件は [英語 README の Scope](README.md#scope) にまとめています。

## AI の利用と責任

Google Gemini が、書きかけの JSON 文書をスキーマの制約に従って最後まで書けるか、という問いを提案しました。
OpenAI Codex は検査器の実装、バイト列とトークン列の計算、得られた証明書の検査に使いました。
AI は関連文献と開発元の既報を調べ、報告の下書きと説明文の編集を行いました。GPT-6-astra は文章の点検に使いました。
外部の生成ツールで観測した結果の一部は、別の AI が自分で書いたテストと JSON Schema 検証器で照合しました。この検算に人間による査読は含まれません。
著者の承認を受けた 2 件の issue 投稿には Anthropic Claude Code を使いました。
文章点検以外の作業では、使用したモデルの版は記録されていません。
著者の滝本竜彦がコード、データ、本文の結論に責任を負います。

## ライセンスと連絡先

コードは Apache-2.0、独自文書・生成データは CC-BY-4.0、第三者資料は元の条件に従います。[LICENSE](LICENSE) と [第三者資料の出典・条件](THIRD-PARTY-NOTICES.md) を参照してください。使用した道具・データへの謝意は [英語 README](README.md#acknowledgements) に記しています。

研究の連絡先：滝本竜彦（Tatsuhiko Takimoto） <research@tatsuhikotakimoto.com>
