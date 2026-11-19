# 固定語彙における token 完結の保証

## 1. 入力とdecoderの意味

前段で検査済みの全域byte DFA A=(Q,δ,q0,F) と、有限の通常token集合V、各tokenの非空byte片h(v)を入力にする。未指定byte辺はsinkへ行く。対象言語は既存のcanonicalな有効UTF-8 JSON言語L(A)。

今回のhは [固定GPT-2 tokenizer.json](https://huggingface.co/openai-community/gpt2/blob/607a30d783dfa663caf39e06633721c8d4cfcd7e/tokenizer.json) のByteLevel文字表を逆にしたもの。通常tokenは50,256個、EOSは50256で通常集合から除いた。byte/Unicodeの対応と、byteを結合してからUTF-8へ直す順序は [tokenizers 0.23.3のByteLevel実装](https://github.com/huggingface/tokenizers/blob/v0.23.3/tokenizers/src/pre_tokenizers/byte_level.rs) を確認した。

ここでは **h(v1)…h(vk)自身が有効なcanonical UTF-8 JSONになる列**を認める。tokenizerの最終text decoderが不正UTF-8をU+FFFDへ置換して初めてJSONになる追加の列は含めない。その広いlossy-text解釈の最短性は未証明。prefixがUTF-8途中でも、全列が最後に有効UTF-8になればよい。suffixだけをtextとしてdecodeした結果は判定に使わない。

これは固定語彙の通常IDを自由に選ぶ模型であり、BPE encoderが一つに決める分割に限らない。既にあるtoken prefixは書き換えず、後ろへ通常IDを足す。文脈依存のdecoder、外部token filter、logitsの非零確率、samplerの終了は別問題である。

## 2. byte DFAの縮約

生成器は受理/非受理から始め、受理flagと各byteの遷移先classで分割を反復する。検査側は最小性を仮定せず、写像π:Q→Qbarの全域性、root/sink/受理、全byteについて

```text
π(δ(q,b))=δbar(π(q),b)
```

を検査する。両方が省略するbyteはそれぞれのsinkに行くため、辺keyの和集合とsink対応を確認すれば256 byteを覆う。入力byte DFAの証明は先に別入口で検査する。上の条件からbyte列の長さの帰納で、縮約が言語とprefixの将来を保つ。

最小性そのものはtoken完結の正しさに不要で、縮約は規模を小さくする実装上の工夫である。#895は元54,842状態から13classになる。

## 3. 語彙との合成

token境界での遷移を

```text
δV(q,v)=δbar*(q,h(v))
```

と定義する。token列の長さの帰納から、δV*(π(q0),v1…vk)=δbar*(π(q0),h(v1)…h(vk))。従ってこのtoken DFAの言語はh^(-1)(L(A))である。byte片が文脈非依存なので、token境界のstateはQbarだけでよい。語彙pieceの途中をtoken完結の状態と誤認しない。

生成側は語彙trieを各classから走査して遷移を作る。sinkへ入れば残りのpieceを走査せず捨てる。同じ遷移先へ行く通常IDをまとめ、最小ID・個数・全ID列のSHA-256を保存する。最小ID以外の同一遷移先のIDは、同じ長さの辞書順最小の完結で最小IDに優越しない。

別検査器verify.pyは生成器をimportせず、語彙trieも使わない。全classから全通常tokenを一つずつbyteで再生し、全遷移groupを再構成して照合する。独立processではproduce/generate/NFA builderの読取りをaudit hookで拒否する。共有するのは固定のtokenizerの意味/byte写像、hashとbyte表示の小関数、及び旧byte検査の信頼核。第二の独立したSchema意味実装や形式認証ではない。

## 4. 最短性、不能、EOS

各token辺のコストを1とし、受理stateから逆BFSで距離を付ける。受理は0、他は有限距離の子の最小+1、該当する子がなければnull。検査器は全辺に対してこの式を検査し、添付token列の長さ・距離減少・実再生・同長時のtoken-ID辞書順も確認する。null集合は受理を含まず外の有限距離stateへ出ないので、tokenでの完結不能の閉包資料になる。

prefixのbyte列を元DFAで再生し、πで到達stateを得る。そのtoken距離と証拠を返す。与えられた通常token prefixについてもpiece連結がそのbyte prefixに一致することを確認する。byte-fallback列は別の到達可能性の証人であって、BPE encoderの唯一の分割を主張しない。

通常tokenから受理stateまでの最小個数を主距離とする。EOSは受理時だけ許し、明示EOSを含めるなら距離は+1、列には50256を一つ足す。すでに有効な完結prefixなら通常token距離0、明示EOS込み1である。

## 5. なぜ今回のtokenだけの不能は0なのか

固定語彙には全てのb∈{0,…,255}についてh(f(b))=bとなる通常token f(b)がある。byte完結w=b1…bnが存在すれば、token列f(b1)…f(bn)は同じwを出して受理する。逆にtoken完結はpiece連結を通じbyte完結になる。従って全てのbyte状態で

```text
byteで完結可能 ⇔ tokenで完結可能,
可能なら token最短距離 ≤ byte最短距離。
```

これは今回の83件だけの探索的な不発ではなく、このbyte完全な固定語彙に対する性質である。実測でも56,182 byte-live stateと320 byte-live prefixで0を確認した。12件の空言語を71件の非空言語と混ぜて根の成功数を水増ししない。

有効UTF-8の完結を構成できるので、後段にlossy decodeを許してもその存在は失われない。しかし追加の置換経路が最小個数やtie-breakを変えないとは示していない。最短性の範囲は1節のstrictなraw-byte模型である。

## 6. 既存toolとの接続と上限

XGrammar 0.2.8のnative BYTE_LEVEL変換は全50,256通常pieceと一致した。llguidance 1.9.1は50,255 pieceが一致し、ID187（FF）だけを特殊扱いしdecode_bytesは空だった。全83 byte DFAでFFからbyte-live stateへ行く辺は0、native maskでもFFは許されなかった。従ってこの差は今回のcanonical UTF-8言語の完結可能性を変えない。Outlinesへは検査したraw piece表を渡した。これらのmetadata確認を、全てのbackend文法が元Schemaに忠実である証明とはしない。

保持状態/arcの上限は、元byte state、縮約state、token境界state、98,024語彙trie state、作業frontier、まとめたtoken arcを合わせ50万とした。各classの辞書走査を流して辺を作るので、全ての字句途中の(q,trie-node)を積graphの頂点として保持しない。累積字句訪問回数は別の作業量であり、本走行の最大658,848回を隠さない。CPU/wallの上限はその作業も含める。

UNKNOWNは時間・RSS・state/completion予算の打切りで、EMPTYとは分ける。本走行83件のUNKNOWNは0、最大保持数152,950だった。cap2の人工対照はUNKNOWNを返し、byteを欠く人工語彙では実際にbyte-live/token-deadを検出した。これらをGPT-2の実例には数えていない。
