
Creating FPH>HRNS and HRNS>FPH maps


The SQLite DBs are created


=== Creating seed entities =====================================================================================================================================


entity FPH: 6b02c0312ef64f0127deaf85e2221bbb > global
parent namespace FPH = 99aa06d3014798d86001c324468d497f > 
entity type = namespace
active? yes

entity FPH: 729b28a769834bd60f66a35b656c67b0 > hours.global
parent namespace FPH = 6b02c0312ef64f0127deaf85e2221bbb > global
entity type = currency
active? yes

entity FPH: 1fa6643de323b807d2f712cb6cc2b701 > hours.gaia.global
parent namespace FPH = 230d378de93d1dc090841a9db4fa56c6 > gaia.global
entity type = account
active? yes

entity FPH: 230d378de93d1dc090841a9db4fa56c6 > gaia.global
parent namespace FPH = 6b02c0312ef64f0127deaf85e2221bbb > global
entity type = primid
active? yes

----------------------------------------------------------------------------------------------------------------------------------------------------------------

6b02c0312ef64f0127deaf85e2221bbb > global
729b28a769834bd60f66a35b656c67b0 > hours.global
230d378de93d1dc090841a9db4fa56c6 > gaia.global
1fa6643de323b807d2f712cb6cc2b701 > hours.gaia.global


Entities in temporary lists:

	6b02c0312ef64f0127deaf85e2221bbb	global
	729b28a769834bd60f66a35b656c67b0	hours.global
	230d378de93d1dc090841a9db4fa56c6	gaia.global
	1fa6643de323b807d2f712cb6cc2b701	hours.gaia.global


----------------------------------------------------------------------------------------------------------------------------------------------------------------


Press ENTER to continue...
Create full quasi-TLD root namespace set? [yN] 
=== Creating reduced quasi-TLD root namespace set ==============================================================================================================


ab47a0336c35249e1f72901e78a60be3 > uk
16c429bd070dddd9d5a2a53821ed7e7a > es
35743bb66050829bab154f820778087b > fr
05a9d7bd4b47de131abe87e45f3c3356 > de
3a00e06f17b749cf9ace2b6431b7f1be > ca
806b97575ac869cc0c148472ce4bd39d > us


=== Generating fake entities ===================================================================================================================================

How many fake entities should be created initially? 
No value entered. Therefore using the default value 200.

The number of accounts will be far greater than that of the other entitity types
so a further 100 accounts will be added.

Please wait while a set of 300 fake entities is created, more than 100 of which
will be accounts. This may take some time because the dependency rules must be
followed.

--------------------------------------------------------------------------------
entity	entity       error
 count	type         count    entity FPH                       > entity HRNS
--------------------------------------------------------------------------------
     0	namespace        0    07599ba522c29b6a56db8fa930dcfead > va.es
     1	namespace        0    4c059dd85eb18d7de7147487f594e69c > ob.de
     2	account          0    12ed445c2a7c87e2e0df8e0977aedc9d > vi.ca
     3	currency         0    04cb9920d37578f7a3d99259e3604f9f > rd.fr
     4	namespace        0    bebbeda9bac5312125db96068c76f74d > ng.ca
     5	currency         0    b782b7fe8f48727c1cd44b8d3504d9d5 > qe.de
secid jdl.global (bf084de388bc8401cf3390ed91d8b487) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
     6	secid            0    bf084de388bc8401cf3390ed91d8b487 > jdl.global
secid cfy.es (fad0d7cebaed87b809ba5e98621eb6f3) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
     7	secid            0    fad0d7cebaed87b809ba5e98621eb6f3 > cfy.es
     8	namespace        0    7fdac4de93423c6cc65514707ee93acb > kg.ca
secid hww.ng.ca (dcdbca187c3861f40e8981bff0c9b250) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
     9	secid            0    dcdbca187c3861f40e8981bff0c9b250 > hww.ng.ca
secid hf.ng.ca (b087459f6cb759f37d19167e1d143f1d) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
    10	secid            0    b087459f6cb759f37d19167e1d143f1d > hf.ng.ca
    11	primid           0    44380c8a24e2d8b90d007b070a7535e1 > nfx.ng.ca
    12	currency         0    2fd22e8aebcf7da80c602f8123743fe8 > sro.fr
    13	namespace        0    c0be9e3af3f43a972a9ef749a4849f76 > ekc.kg.ca
secid xhi.va.es (1ea5fa48ae44dbb88f6e670208d41705) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
    14	secid            0    1ea5fa48ae44dbb88f6e670208d41705 > xhi.va.es
    15	account          0    3287a0a73918eb0f29699977d5b8700b > rd.ekc.kg.ca
    16	currency         0    c173853b254e7e8e26e40f85b04a508b > kh.us
    17	currency         0    89a565572c4b5deeb5a05fc45f041b6d > kmz.es
secid zgv.es (7fa6b97407cbec748786cbce8edc3f7c) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
    18	secid            0    7fa6b97407cbec748786cbce8edc3f7c > zgv.es
secid nz.uk (4151e1ba3270fe08c22a252e543136a0) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
    19	secid            0    4151e1ba3270fe08c22a252e543136a0 > nz.uk
    20	namespace        0    d0510df588dec074281648960b43e13a > pza.uk
secid cad.ob.de (d1c3e9f53ab13535212c751bc894a9c6) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
    21	secid            0    d1c3e9f53ab13535212c751bc894a9c6 > cad.ob.de
secid hm.ca (a3bb8bfe2836d14792fa2afac41d0805) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
    22	secid            0    a3bb8bfe2836d14792fa2afac41d0805 > hm.ca
    23	primid           0    a04533bc69b322f35876f8843aa47c35 > btv.ng.ca
    24	account          0    a149e3b997273a47d2cbfa155e6e463b > yyd.es
    25	currency         0    e4aae6a04a41ee0a2ed7ceb4b2f732f6 > qig.pza.uk
    26	namespace        0    54f3baf0e4e6cdb71d9b02e30885e74d > dt.va.es
    27	currency         0    05e8db2ee75d416fced1ddf517897988 > yfy.es
    28	account          0    97d107a4de332962b46baf1595554196 > xx.uk
    29	namespace        0    d71435accde68233d9db45b19e2ee055 > nvp.ng.ca
    30	account          0    db557d0b11f11d19d56f9f1ee92c4ed6 > qs.global
secid fav.ekc.kg.ca (b883ea840c7d1101f6768eeebfa79d69) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
    31	secid            0    b883ea840c7d1101f6768eeebfa79d69 > fav.ekc.kg.ca
secid gvt.global (4aa7a331ac2ab9c9cf0a0b3a18d0bd44) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
    32	secid            0    4aa7a331ac2ab9c9cf0a0b3a18d0bd44 > gvt.global
    33	primid           0    4ee0f3febc7899573d7ec517c9541d5d > bjr.nvp.ng.ca
    34	currency         0    6f8ca62120032250d1a41378d25409a5 > qd.fr
secid zkj.va.es (5250869a9d3202b710be8e82d4b98d0c) added for primid btv.ng.ca (a04533bc69b322f35876f8843aa47c35)
    35	secid            0    5250869a9d3202b710be8e82d4b98d0c > zkj.va.es
    36	primid           0    a22ddf10716f470caa95b56039797f29 > ty.us
    37	namespace        0    b90ae5aa55a6479746e26bb59ec0b6bf > kkm.us
    38	primid           0    16f565fd51da062d20a880e6f6d7d0f3 > zpt.uk
secid ln.kkm.us (f8f6a48cd3a2bd3128d59bb47669d52a) added for primid ty.us (a22ddf10716f470caa95b56039797f29)
    39	secid            0    f8f6a48cd3a2bd3128d59bb47669d52a > ln.kkm.us
    40	primid           0    75ab19a0aa8f2e4f0bbf1b9c7fc3d837 > hdm.global
    41	namespace        0    30ebb0a47f312588af032056a367fdc3 > ck.uk
    42	currency         0    902ba7e49efe710ee128e83d120b8490 > gkq.ca
secid fvv.ca (36ddf4caa248a91f20e8171b10493278) added for primid bjr.nvp.ng.ca (4ee0f3febc7899573d7ec517c9541d5d)
    43	secid            0    36ddf4caa248a91f20e8171b10493278 > fvv.ca
    44	primid           0    3683ab4e21661037141c563b0a6a41d2 > qr.es
    45	namespace        0    e39116a30a7a72287cca2fb501ea78aa > gxo.ng.ca
    46	account          0    c6218d94c43b01a9d30b50dd9980badd > qcc.ng.ca
    47	account          0    9fb4344ed7b2634fb9d769e075e64eee > dop.kkm.us
    48	namespace        0    c416637beeda4e98bfcbdfeed8cf6533 > xv.ob.de
    49	account          0    b5db2611cdb12fcf22db0599226caca8 > zj.us
    50	account          0    87d7983d3ac4463291b2856644cad48a > tev.ca
    51	namespace        0    4390247c51e5ba47b9199b781ad272e4 > ypz.pza.uk
secid pl.ob.de (eac6ecb33421b201bca7010ebb4d3bb1) added for primid btv.ng.ca (a04533bc69b322f35876f8843aa47c35)
    52	secid            0    eac6ecb33421b201bca7010ebb4d3bb1 > pl.ob.de
    53	primid           0    5bcdf2e78cec8a71c1b8cb81ab56cc87 > zrq.uk
secid ny.nvp.ng.ca (338be10606e90e757d6942fbc16c2e2b) added for primid qr.es (3683ab4e21661037141c563b0a6a41d2)
    54	secid            0    338be10606e90e757d6942fbc16c2e2b > ny.nvp.ng.ca
    55	namespace        0    02fc4ab96594ce3c7ee235fd4d0594d5 > xyd.fr
    56	primid           0    de6fc534cf3dd6d678762f6a7cfaf4dd > dnw.fr
    57	namespace        0    8e12442ad3dc0ce23fc8f478eb34ea41 > qkh.fr
    58	namespace        0    2f073be27c2970ef2de8c879e6962391 > lqe.kkm.us
secid do.de (d5281a96d12e9c719ec4f3a4c3356be9) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
    59	secid            0    d5281a96d12e9c719ec4f3a4c3356be9 > do.de
    60	primid           0    a010812f797d311d27ee3baf2cb06744 > nv.xyd.fr
    61	account          0    95bf3f2a19e53a5a8d8f26af0fb5124e > xdl.qkh.fr
    62	namespace        0    3f468785de296f14d9f01a37db3cd60d > dqu.ob.de
    63	currency         0    9dcc7a87299c749224d281f98bf4bff4 > un.xyd.fr
    64	currency         0    28f198b3861ef1b8bf15f9c0da8d2c87 > js.pza.uk
secid cl.va.es (45da6e8c991da75034e984d5ab9d106f) added for primid bjr.nvp.ng.ca (4ee0f3febc7899573d7ec517c9541d5d)
    65	secid            0    45da6e8c991da75034e984d5ab9d106f > cl.va.es
    66	currency         0    7654b814f9bc7935f331342d1977b857 > yiq.qkh.fr
    67	currency         0    fe953be96261919e90b04e9fd7db02cc > ls.us
    68	currency         0    4607b4cf33c22c377a389fba8fe489c9 > jq.ca
    69	account          0    c5b10d20f4b28160658fa92039cd27f6 > tyj.dt.va.es
    70	primid           0    75507a1e2d54d081eb1074cee766ff90 > gp.ng.ca
    71	currency         0    85223b5ddf29a7097fb6847ff25d1242 > vst.ob.de
    72	currency         0    5c4301e3e4c2a28e4075b794652e763b > ei.dqu.ob.de
secid it.ck.uk (de393a846425a9ded1377d7d8cc3fc36) added for primid nv.xyd.fr (a010812f797d311d27ee3baf2cb06744)
    73	secid            0    de393a846425a9ded1377d7d8cc3fc36 > it.ck.uk
    74	account          0    23f9752ab721ba425f1173d6d972ab21 > zn.ob.de
secid xcv.kg.ca (a4076757f5138b360de0f2e2ef69698e) added for primid btv.ng.ca (a04533bc69b322f35876f8843aa47c35)
    75	secid            0    a4076757f5138b360de0f2e2ef69698e > xcv.kg.ca
    76	account          0    f02a6d0e93792c0be7c22e8ffb082686 > cej.ypz.pza.uk
    77	namespace        0    ae6763b1e85131452ea0ffa31f0e3fd2 > kez.ekc.kg.ca
    78	primid           0    818539b52ce5f51298ece53de83f3f50 > jbu.xv.ob.de
    79	primid           0    341c8750ddc4543fda8a287b66db2811 > im.us
    80	namespace        0    9fbc547b6865ba01d50cf71744212e50 > vpa.uk
    81	account          0    5907aff958ae0a98cc92dfd10fc28694 > lz.ypz.pza.uk
    82	account          0    de5f083a0e10dc8680b36ece8d7ed6bd > ds.ypz.pza.uk
    83	namespace        0    22ab9dca3e4dca0627e1e5549c6a745c > kx.uk
    84	currency         0    1138ed029ddc56663c3cb731f61374c1 > lcc.ck.uk
    85	primid           0    54737ff35ca8fef88db3582c58d7425d > ec.kez.ekc.kg.ca
    86	namespace        0    d63abac18e68ee1bdd50a9a347981bc2 > lbp.xyd.fr
    87	account          0    5a995c57bb312925dfb899ff0be0237c > yg.ck.uk
    88	namespace        0    127adfac6e921a978c772f5d37a7517e > nu.kez.ekc.kg.ca
    89	currency         0    d943d0a9bc6eeb55916f1da41fb018f0 > ut.kkm.us
    90	account          0    53e2f4a2a5b91b96f2519e334a8d484e > ge.pza.uk
    91	primid           0    fd16a0b32c0611ac3d6cbe327bfebdce > fu.es
    92	account          0    043b201e72ebc69d3ea13d4327ce9fc7 > xel.vpa.uk
    93	primid           0    716e2382dc02094a66ef79e77aaab141 > xtn.xyd.fr
    94	account          0    34ba01cadd15d9885316f72375e8feb2 > hj.lqe.kkm.us
    95	currency         0    01d4d9055ed4e8638503f3f104211b2b > jr.global
    96	account          0    f7f4ae3ffe178a22534a74a1774bef5d > xp.pza.uk
    97	primid           0    d709314b8deb2880a56ad2e034a3fb89 > jvs.ck.uk
    98	account          0    f7195f44cc81dc153c0d2efab0f97438 > vwz.lbp.xyd.fr
    99	namespace        0    8b9832fafc6d1c0091c3852a281820a8 > ic.va.es
secid lp.ob.de (b9611bb298d05e37777da17040735348) added for primid btv.ng.ca (a04533bc69b322f35876f8843aa47c35)
   100	secid            0    b9611bb298d05e37777da17040735348 > lp.ob.de
   101	currency         0    baebadb286f7e11fdd60c3be19cfb065 > wv.xyd.fr
   102	primid           0    c3443839f7e7bf404db9339455306c48 > lnp.fr
secid spo.kkm.us (4e36bb628ad67cfe5d81277f667ae25d) added for primid nv.xyd.fr (a010812f797d311d27ee3baf2cb06744)
   103	secid            0    4e36bb628ad67cfe5d81277f667ae25d > spo.kkm.us
   104	currency         0    d3d16814967be2e8a4e478f37dd1162e > wsd.lqe.kkm.us
   105	namespace        0    13ae257ff4cbb957c075b661263d189f > ooz.ng.ca
secid ocj.pza.uk (12830d641e0d26fa7559bc5f8a83509a) added for primid lnp.fr (c3443839f7e7bf404db9339455306c48)
   106	secid            0    12830d641e0d26fa7559bc5f8a83509a > ocj.pza.uk
secid iw.es (4f26ebdf21b45e74b8b454ac970b4832) added for primid dnw.fr (de6fc534cf3dd6d678762f6a7cfaf4dd)
   107	secid            0    4f26ebdf21b45e74b8b454ac970b4832 > iw.es
   108	account          0    0312e11a30374824a6a337ef74b8ec92 > pr.xyd.fr
   109	account          0    5b8c0eead99ed0b8b8a469f80b32fb7f > fy.ypz.pza.uk
secid wx.ekc.kg.ca (2ecba9418f99d8a0b18007779723ca69) added for primid nfx.ng.ca (44380c8a24e2d8b90d007b070a7535e1)
   110	secid            0    2ecba9418f99d8a0b18007779723ca69 > wx.ekc.kg.ca
secid lo.us (c50f9a1c96bd7aa7ac4e358c3384a05e) added for primid im.us (341c8750ddc4543fda8a287b66db2811)
   111	secid            0    c50f9a1c96bd7aa7ac4e358c3384a05e > lo.us
   112	namespace        0    ddedd86242aab7e2fb76a41026df5ab3 > ts.de
secid nx.ts.de (ff033f52a0875130527257e41f09ebcf) added for primid bjr.nvp.ng.ca (4ee0f3febc7899573d7ec517c9541d5d)
   113	secid            0    ff033f52a0875130527257e41f09ebcf > nx.ts.de
   114	account          0    12f02e9f0e0dc7ec73ef87ffcd1b536d > pl.lqe.kkm.us
   115	namespace        0    41e54f8f73322267dd9584124bdc9e9e > yh.dqu.ob.de
secid vso.vpa.uk (bf8dbab172006fdd69838b1b5bc54754) added for primid ec.kez.ekc.kg.ca (54737ff35ca8fef88db3582c58d7425d)
   116	secid            0    bf8dbab172006fdd69838b1b5bc54754 > vso.vpa.uk
   117	primid           0    c61491ca17df43cde0093ac9eb8018e7 > pz.ng.ca
   118	namespace        0    a7719721fd6975d5aa4f177a23465efc > qvb.nu.kez.ekc.kg.ca
secid saz.dt.va.es (14d506ac13e1498a4534fe3e42e898ae) added for primid gp.ng.ca (75507a1e2d54d081eb1074cee766ff90)
   119	secid            0    14d506ac13e1498a4534fe3e42e898ae > saz.dt.va.es
secid cwa.uk (b496316e5bcd44647b4e60f7c04d3c01) added for primid fu.es (fd16a0b32c0611ac3d6cbe327bfebdce)
   120	secid            0    b496316e5bcd44647b4e60f7c04d3c01 > cwa.uk
secid dw.kez.ekc.kg.ca (71e727b4e6e30fa0f21ca96153cfe24f) added for primid zrq.uk (5bcdf2e78cec8a71c1b8cb81ab56cc87)
   121	secid            0    71e727b4e6e30fa0f21ca96153cfe24f > dw.kez.ekc.kg.ca
   122	currency         0    9963b48f14137583c83c58b2865d5ecb > kno.ts.de
secid rwn.kez.ekc.kg.ca (955fa2e58f22952e52e2a6eaa1b2ab12) added for primid fu.es (fd16a0b32c0611ac3d6cbe327bfebdce)
   123	secid            0    955fa2e58f22952e52e2a6eaa1b2ab12 > rwn.kez.ekc.kg.ca
   124	namespace        0    45ac9da9c718c3b20c917ae6c1061b53 > wk.ca
   125	currency         0    059fcfc4b658bad8643f3060a12f4fca > trw.vpa.uk
   126	primid           0    98924c1f16d41c0268139685bca3d15f > xiu.kkm.us
   127	primid           0    f4af3facd956883def3fe94d4ff24ffb > jx.es
   128	namespace        0    c17cdc81d9f99cbb2dd4b650c2884ea2 > wfa.vpa.uk
secid lag.pza.uk (2ad44c6e4ab93fc1d8d72512b9446d4b) added for primid nv.xyd.fr (a010812f797d311d27ee3baf2cb06744)
   129	secid            0    2ad44c6e4ab93fc1d8d72512b9446d4b > lag.pza.uk
   130	currency         0    cb4c6bf63a7d67faaf9f2110ff4677c2 > wxr.uk
secid pc.gxo.ng.ca (9f6a875aa72cf6bf891c74d1b4087d8d) added for primid jvs.ck.uk (d709314b8deb2880a56ad2e034a3fb89)
   131	secid            0    9f6a875aa72cf6bf891c74d1b4087d8d > pc.gxo.ng.ca
   132	primid           0    5baff99f4c6af16a17268ac43618374b > zll.ts.de
   133	primid           0    83eeb0195d0a586cde2de1ba0737f3d0 > twb.dt.va.es
   134	primid           0    9e07fcf437e19069de2d4ef81bc5fb3b > vs.nu.kez.ekc.kg.ca
   135	namespace        0    8a7ed34abe9f1c72006d056bb8b97440 > qg.nvp.ng.ca
secid ze.kx.uk (2e51a75c24914d26820119d1caa7213e) added for primid jvs.ck.uk (d709314b8deb2880a56ad2e034a3fb89)
   136	secid            0    2e51a75c24914d26820119d1caa7213e > ze.kx.uk
   137	namespace        0    91a819dd4135026b8de700257296172c > hdf.kkm.us
   138	currency         0    66aa82874fe249acb7b2c3e5cd855bb5 > jkm.us
   139	currency         0    26836f512a329a555007b3c9fc3dfe4d > bx.ca
   140	account          0    a9a9ab009ad5402c3ddf122587c8d15b > yo.hdf.kkm.us
   141	currency         0    96c47cae4501eb2bb8b979163f898cd6 > dd.global
   142	primid           0    a6286078668dceed009c5f5394d2203e > zj.yh.dqu.ob.de
   143	currency         0    c9833f467d7a93d442d71495a965d869 > ejo.wk.ca
   144	account          0    deb002e2b52ef4244ee3655b73403ab0 > ufi.nu.kez.ekc.kg.ca
   145	account          0    c193e7726be0a4f36b8a157bae6f9bbe > fch.fr
secid mou.qg.nvp.ng.ca (dd5e0f754e3b5a38d11e23debe7058ad) added for primid lnp.fr (c3443839f7e7bf404db9339455306c48)
   146	secid            0    dd5e0f754e3b5a38d11e23debe7058ad > mou.qg.nvp.ng.ca
   147	currency         0    bf5237aad952878e80d015dc110f323a > nu.yh.dqu.ob.de
secid dn.ypz.pza.uk (82f91f8f56409e5e813452e9bfcae272) added for primid xtn.xyd.fr (716e2382dc02094a66ef79e77aaab141)
   148	secid            0    82f91f8f56409e5e813452e9bfcae272 > dn.ypz.pza.uk
   149	account          0    56e9d9fe8700d3ae86be0fc757912c98 > rnu.ypz.pza.uk
   150	namespace        0    68718a1f45f18e58c85ec24ad3d52f3d > ozh.vpa.uk
   151	primid           0    5cc5ca984d8afe4e525e902352656889 > wi.es
secid afn.dt.va.es (4762effa98ec3d45a73653eb3e81b179) added for primid vs.nu.kez.ekc.kg.ca (9e07fcf437e19069de2d4ef81bc5fb3b)
   152	secid            0    4762effa98ec3d45a73653eb3e81b179 > afn.dt.va.es
   153	primid           0    a3e7d8219895ef56c227698a07aedd5b > fz.es
   154	namespace        0    254c657a0dff426a265738fe509b68a7 > hd.uk
   155	account          0    2e60d7073e850258b461807f6a76bef9 > ehp.ob.de
   156	primid           0    abc51d8bb1cb9b48b72dc40adace88d4 > wlj.global
   157	primid           0    3e34420d692dc567fc845d1c9d78477d > vj.fr
   158	namespace        0    b896fb6c93f002dfcbd128d731e392c4 > ne.global
secid kpp.dt.va.es (876853ed9d989c69ce2a99e3b6f28d93) added for primid gaia.global (230d378de93d1dc090841a9db4fa56c6)
   159	secid            0    876853ed9d989c69ce2a99e3b6f28d93 > kpp.dt.va.es
   160	currency         0    c9cff4d617ccb9b8b1ddc0c34a490b10 > byz.ozh.vpa.uk
   161	account          0    d31d36bd6b7de2e0d1091a71cb440f79 > npx.ekc.kg.ca
   162	account          0    6d6f181cfa28726e7c20ba7ea06a57a5 > uyp.de
   163	primid           0    6e8cc15f73c7709c02a3faa99181fc0d > oqv.ozh.vpa.uk
   164	account          0    0e0b8e68a71bc5b8643b3c2091890bd0 > nu.de
   165	currency         0    aa61088ca386cef609102b092cc4f03c > tn.us
   166	primid           0    092ba95db1a73125471313319a3f38db > pe.qg.nvp.ng.ca
   167	currency         0    03f46eb2c58bc64aae20ac5b108ad49f > tdq.yh.dqu.ob.de
   168	namespace        0    944867c16207f3f0c1adbb8df95b6417 > ej.ozh.vpa.uk
   169	account          0    3f1cf5819b61792b93f316b6132ac5f5 > wd.uk
   170	account          0    b82fa25574fdcaed3e125f8f35011b78 > ws.fr
   171	primid           0    a60884cc92dd114aafda78ec75092687 > yzc.ozh.vpa.uk
   172	currency         0    c61d794e6b0e8ae4897696b949af8e6b > emj.ej.ozh.vpa.uk
   173	namespace        0    4fd24a2b624a90c12423896e0634bf15 > lks.wfa.vpa.uk
   174	namespace        0    59f74812891142513fc912512be35a29 > eds.lbp.xyd.fr
   175	primid           0    17fd1234021d304a21a9e3dab74e5503 > hp.eds.lbp.xyd.fr
   176	currency         0    078a9158378c5e6e27ff4dc3032edc3d > hm.nvp.ng.ca
   177	currency         0    d9b69cbf2e6cc035b5b1cce15f73112b > gn.xv.ob.de
   178	account          0    002f617b8c6afb2d74fe9f2e93b9adbc > usf.uk
   179	primid           0    af86d25f23496717e55cdb94aad25880 > lj.hd.uk
   180	account          0    38b266925ede118dcba77c49b2721b4f > rf.kez.ekc.kg.ca
   181	account          0    0444ab629e78b8f7e81ced3fa82a527f > ud.kkm.us
   182	namespace        0    6a8b9c16377b528e6e391fd798c781b9 > kel.lbp.xyd.fr
   183	namespace        0    e72a9c8e466ef2326491ea0715c73165 > rje.eds.lbp.xyd.fr
secid vn.kez.ekc.kg.ca (244ad5d2142ac96d4973b07edbe00916) added for primid wi.es (5cc5ca984d8afe4e525e902352656889)
   184	secid            0    244ad5d2142ac96d4973b07edbe00916 > vn.kez.ekc.kg.ca
   185	primid           0    0513aaca6abc6e6ac47c32f045514b51 > izp.ne.global
   186	primid           0    0fe8783f77c67f9b0c84142245b6f82a > cv.kg.ca
   187	namespace        0    97f17e76c14072e185d33a57e3c40574 > opj.fr
   188	namespace        0    551b2c7c15626242819ea6ba31fe8420 > fzf.es
   189	namespace        0    ee1ce4bfa9b163b2a7fca7783a4a2524 > jzl.global
   190	currency         0    32cdd7816263ad5b78a443f71d6eac2e > at.hd.uk
secid xj.qg.nvp.ng.ca (f20876bd44cac1718fdecf234df3b262) added for primid izp.ne.global (0513aaca6abc6e6ac47c32f045514b51)
   191	secid            0    f20876bd44cac1718fdecf234df3b262 > xj.qg.nvp.ng.ca
   192	account          0    81dae1c458ca110e27f32f09831f19ab > chn.kkm.us
   193	account          0    4c41834a21a56f4808ff2025d347b50d > mmc.ca
   194	namespace        0    e3c7c4560eea40b195695e32ddfb4951 > qmt.ypz.pza.uk
   195	currency         0    db6c4b9a951bb43fc15a1b6950040a6b > fl.vpa.uk
   196	namespace        0    acaf2ec94aecb6775434c325b36b6544 > ycl.lks.wfa.vpa.uk
   197	namespace        0    eb7a92e3840d04e06b6d1df37e3d6e3f > op.hdf.kkm.us
   198	namespace        0    eb54199ec0a24e8750c58ab34c8f07dc > qk.ob.de
   199	account          0    78a3b573eddb3e4a8db36b919230c3d2 > ur.hdf.kkm.us
   200	account          0    c705733cc03506a0deec7bbec309d813 > yrq.nvp.ng.ca
   201	account          0    83436a9e79c8b1ad6b1064252daefc0a > tsu.lbp.xyd.fr
   202	account          0    52e021cd90dc34e6bcfe673da7caeb53 > fv.kg.ca
   203	account          0    203f4efb0fa2ece0c08b1722f00af5bf > jk.kel.lbp.xyd.fr
   204	account          0    8cd5e085be172d4c1d688e761d9479a7 > nwi.vpa.uk
   205	account          0    50d4e5ae77820fb6ef594a348bd6e00c > rgn.qmt.ypz.pza.uk
   206	account          0    7ac890b984e9c0c3697103bbaf38f4f4 > btw.jzl.global
   207	account          0    e3149a26dffbf86d34ffc87ca4c04e3a > vz.qkh.fr
   208	account          0    612d9375b4a7295f27c1ffbc44a86938 > cg.xyd.fr
   209	account          0    757924a7316c81a44560f81dbb58264b > ze.gxo.ng.ca
   210	account          0    3dfb07d9ea1d0551d8f65f6b872ed7a3 > gar.hdf.kkm.us
   211	account          0    f24bce327b129beb52d0a1cafc75b1ab > srz.ob.de
   212	account          0    c994d285b2d9485c9a8435ad695efcef > hfy.ic.va.es
   213	account          0    1647b7db08603d501f5681b70df030a6 > lqc.pza.uk
   214	account          0    c9a4d37c25a57f96c830311d84c69d87 > tjg.kx.uk
   215	account          0    ec022d4e4f3b6618ceb4d58de96fa043 > mdn.dt.va.es
   216	account          0    0c1833e2b635ff601e300be6799f9d0f > lts.jzl.global
   217	account          0    d57d4f1d718ad6fd83e0e2be036cf1c8 > jgb.xyd.fr
   218	account          0    605eafbe93848a780f942e427c24ed47 > nu.hd.uk
   219	account          0    db04c7acbe5be4502a3beb7cfa3ad088 > fo.opj.fr
   220	account          0    bfdd83d1c100402c4c5f631267afe3be > cne.qk.ob.de
   221	account          0    3bea4ecadd1ccc16b7ed88fbcff77d34 > nv.yh.dqu.ob.de
   222	account          0    dbf2e864ad009b627167106cce464e54 > hoa.fr
   223	account          0    31316cb7ff5ca66269a01b28edbefc15 > cnz.eds.lbp.xyd.fr
   224	account          0    0b4e2b7cd8b0416fd3eb13bc25441a8f > tdo.wk.ca
   225	account          0    a59e208ddec5106a9b2858343be3fd0f > unm.nvp.ng.ca
   226	account          0    31f0d59397979243f8a3e9c1ddf30aba > wt.xv.ob.de
   227	account          0    e0686ba9c58aff4b6d55d427e1d42866 > agx.de
   228	account          0    d5af58ec02dd85d51744c48537f2519f > xg.hd.uk
   229	account          0    c57d44c00de59c66a80c9e7abd750aa8 > ngw.ne.global
   230	account          0    2cb71c5e8df14be9a2b2f0339e58d9d1 > sni.uk
   231	account          0    26f344bd8185694a0c85806c362297e1 > ns.global
   232	account          1    29189599b7daae96b2a7eb9a208f561c > fx.de
   233	account          1    d0232cae75301912316af37af3ea8b94 > co.hd.uk
   234	account          1    b96ce8c0c64990928e799cfca3d947e4 > tp.kez.ekc.kg.ca
   235	account          1    c8db3f72df96f76ed8b71f00d173ab61 > pbo.ej.ozh.vpa.uk
   236	account          1    c3bac01a2086bf8bc80cdbea88eaf30a > gfe.uk
   237	account          1    23d1096793020b67aa4cdd1c37c1c985 > cvr.yh.dqu.ob.de
   238	account          1    d586349821955225bf179ff7dd428d54 > wi.wk.ca
   239	account          1    48b1c7e2725a5b317cd547f9a4981106 > ki.qkh.fr
   240	account          1    a5dbf07560f1b52aa6a11eb2f9ebd08c > nx.kx.uk
   241	account          1    437f8bca21b5224d299d5cd85c867e46 > ykw.ooz.ng.ca
   242	account          1    57d1c1afec2e7e2305136aab642c2ff9 > sf.kkm.us
   243	account          1    e0aceebb62391352d8a799d6c3875dc2 > kph.qvb.nu.kez.ekc.kg.ca
   244	account          1    4ee958b71bf68dccafd387e98341a25d > uhm.ic.va.es
   245	account          1    ee55d50c7d28ef3edb787c1e69ca6d4d > vpj.uk
   246	account          1    2d8a9ac2b73ae5133c25bbd3ef39d42b > ns.gxo.ng.ca
   247	account          1    474354ae79f876d390d238be0c738a30 > lcc.dt.va.es
   248	account          1    f41f7301e9016c19cc25f998fc2f6a79 > gj.wfa.vpa.uk
   249	account          1    cb72c24e3620f514e80f1167d1231df8 > azl.us
   250	account          1    6ca5640305891b6053b811b8bd35f6f0 > ub.ic.va.es
   251	account          1    3d9d81a3777fa51723f86b5648a04090 > oaa.ozh.vpa.uk
   252	account          1    7fabd56d0d7a5dec90edb62c3a080fca > fst.qk.ob.de
   253	account          1    d0481cb5dee9c5a4b7237b9fce243b33 > qr.fzf.es
   254	account          1    7dfd4b510b5bae54b25a830dba372619 > sf.nu.kez.ekc.kg.ca
   255	account          1    0bbacbcccdcb81c56c96fccb6b177402 > grw.kkm.us
   256	account          1    349851f5b12d9d45ac10d19506bffeba > fh.kx.uk
   257	account          1    9d08001e6bc82b7a3ae49cd96c31fb1a > yxa.kx.uk
   258	account          1    b280f7b0a1a9beb489d76245f6fe2e92 > fr.xv.ob.de
   259	account          1    e266057639c6716105447fc6d1ffcfe0 > sgm.ng.ca
   260	account          1    0081ffe85900eecce9e424bd062844fb > ao.eds.lbp.xyd.fr
   261	account          1    adbb2a09e5ee46c6bf19fef3abe44f71 > oj.lks.wfa.vpa.uk
   262	account          1    ba94b5f3a4dfa4b09a9b4184e1eb2a0c > aaa.ooz.ng.ca
   263	account          1    52d471811087ece350ed3988e375db6e > yi.lks.wfa.vpa.uk
   264	account          1    114959569af908df19fed97c562175ce > owz.us
   265	account          1    e8946be7e347a595086e175224bbb300 > ah.lqe.kkm.us
   266	account          1    0bd122b2695dc052ad79151a3264540d > hr.xv.ob.de
   267	account          1    5b83cf68ccbf215308744afbacf01a79 > ex.vpa.uk
   268	account          1    2a470a5d317633cd5537a99950d1f4bd > ov.hd.uk
   269	account          1    8420598536ab87d1acf2a395e9bc564a > ah.opj.fr
   270	account          1    557dda6065a9f3e16652cfa8d61dd962 > py.ck.uk
   271	account          1    e669dade1ce7966d3502532bc306e91d > veh.wk.ca
   272	account          1    c730ed9e28302912825d485ebde1328b > vpr.vpa.uk
   273	account          1    6c9df333c50ed10a61e3cff6462e7f67 > bcu.kel.lbp.xyd.fr
   274	account          1    3c15e37ab5a785eaccf02bc708bc0112 > hq.us
   275	account          1    f98b0e3b3fc0a73586b38848f8b75af4 > if.ej.ozh.vpa.uk
   276	account          1    8867753ba6e18cf24235dd4ced55a344 > tpj.de
   277	account          1    2f5fa51ef4cc71d95df238514577e27f > hoe.wk.ca
   278	account          1    deae92e9ff21c4b8678624299eac1d0c > bds.ej.ozh.vpa.uk
   279	account          1    b9dc5ae3dfbf918e4211e4e101bee54b > lhk.jzl.global
   280	account          1    65913c61c30970b1a0f449f98a8ad5fc > az.de
   281	account          1    3d4b07c093cc151c2c1b23e198438d53 > hgm.global
   282	account          1    c1371d5d1a0b4009e346973dc4cf9d78 > hx.eds.lbp.xyd.fr
   283	account          1    8d9fb6a8cf2f2aa53dd92529d38879d0 > cwz.kez.ekc.kg.ca
   284	account          1    72da46f1a659be799419b8d5b93c11bd > cc.lqe.kkm.us
   285	account          1    f0a13867d5127a7f6c19903e534648ce > mih.qvb.nu.kez.ekc.kg.ca
   286	account          1    9567206a3b468be28a0f69ec30f6455f > yu.xv.ob.de
   287	account          1    64e6d7ae84f1571a6c538f11f40a81ce > iz.lqe.kkm.us
   288	account          1    b7bbe496a385ad9b74b6e8f2b6a47338 > ju.ej.ozh.vpa.uk
   289	account          1    bd8985ef09579df99946a07ef1175f64 > jmi.qk.ob.de
   290	account          1    d3ba3cdf793beab9e7e1b4795589a584 > pe.yh.dqu.ob.de
   291	account          1    9503a5c312712c41df466211b3f8bc45 > irt.pza.uk
   292	account          1    2c0904fce57727cda50f24dfcebb139c > ld.es
   293	account          1    5bf5450fbe7e222ba6520641a28fda3f > fqb.pza.uk
   294	account          1    4017cf60c26ddde91c97b0f397f1ed89 > vkg.ca
   295	account          1    5c4518b87b9789c4d6c5adfb2ac4d58c > gl.fzf.es
   296	account          1    4cf880c2f31940862eb44cce61527ad5 > lfd.kel.lbp.xyd.fr
   297	account          1    8eb253e11726302e5020a014112aa223 > oj.wfa.vpa.uk
   298	account          1    f79cffba54d8d08043afbe2709bea088 > xg.jzl.global
   299	account          1    363acdfcebe7ac38e0249d14f5566c0e > csr.us

Error count = 1

+----------------------------------+--------------------------+-------------+---------------+
| FPH                              | HRNS                     | entity type | error message |
+----------------------------------+--------------------------+-------------+---------------+
| 4c059dd85eb18d7de7147487f594e69c | ob.de                    | namespace   |               |
| 12ed445c2a7c87e2e0df8e0977aedc9d | vi.ca                    | account     |               |
| 04cb9920d37578f7a3d99259e3604f9f | rd.fr                    | currency    |               |
| bebbeda9bac5312125db96068c76f74d | ng.ca                    | namespace   |               |
| b782b7fe8f48727c1cd44b8d3504d9d5 | qe.de                    | currency    |               |
| bf084de388bc8401cf3390ed91d8b487 | jdl.global               | secid       |               |
| fad0d7cebaed87b809ba5e98621eb6f3 | cfy.es                   | secid       |               |
| 7fdac4de93423c6cc65514707ee93acb | kg.ca                    | namespace   |               |
| dcdbca187c3861f40e8981bff0c9b250 | hww.ng.ca                | secid       |               |
| b087459f6cb759f37d19167e1d143f1d | hf.ng.ca                 | secid       |               |
| 44380c8a24e2d8b90d007b070a7535e1 | nfx.ng.ca                | primid      |               |
| 2fd22e8aebcf7da80c602f8123743fe8 | sro.fr                   | currency    |               |
| c0be9e3af3f43a972a9ef749a4849f76 | ekc.kg.ca                | namespace   |               |
| 1ea5fa48ae44dbb88f6e670208d41705 | xhi.va.es                | secid       |               |
| 3287a0a73918eb0f29699977d5b8700b | rd.ekc.kg.ca             | account     |               |
| c173853b254e7e8e26e40f85b04a508b | kh.us                    | currency    |               |
| 89a565572c4b5deeb5a05fc45f041b6d | kmz.es                   | currency    |               |
| 7fa6b97407cbec748786cbce8edc3f7c | zgv.es                   | secid       |               |
| 4151e1ba3270fe08c22a252e543136a0 | nz.uk                    | secid       |               |
| d0510df588dec074281648960b43e13a | pza.uk                   | namespace   |               |
| d1c3e9f53ab13535212c751bc894a9c6 | cad.ob.de                | secid       |               |
| a3bb8bfe2836d14792fa2afac41d0805 | hm.ca                    | secid       |               |
| a04533bc69b322f35876f8843aa47c35 | btv.ng.ca                | primid      |               |
| a149e3b997273a47d2cbfa155e6e463b | yyd.es                   | account     |               |
| e4aae6a04a41ee0a2ed7ceb4b2f732f6 | qig.pza.uk               | currency    |               |
| 54f3baf0e4e6cdb71d9b02e30885e74d | dt.va.es                 | namespace   |               |
| 05e8db2ee75d416fced1ddf517897988 | yfy.es                   | currency    |               |
| 97d107a4de332962b46baf1595554196 | xx.uk                    | account     |               |
| d71435accde68233d9db45b19e2ee055 | nvp.ng.ca                | namespace   |               |
| db557d0b11f11d19d56f9f1ee92c4ed6 | qs.global                | account     |               |
| b883ea840c7d1101f6768eeebfa79d69 | fav.ekc.kg.ca            | secid       |               |
| 4aa7a331ac2ab9c9cf0a0b3a18d0bd44 | gvt.global               | secid       |               |
| 4ee0f3febc7899573d7ec517c9541d5d | bjr.nvp.ng.ca            | primid      |               |
| 6f8ca62120032250d1a41378d25409a5 | qd.fr                    | currency    |               |
| 5250869a9d3202b710be8e82d4b98d0c | zkj.va.es                | secid       |               |
| a22ddf10716f470caa95b56039797f29 | ty.us                    | primid      |               |
| b90ae5aa55a6479746e26bb59ec0b6bf | kkm.us                   | namespace   |               |
| 16f565fd51da062d20a880e6f6d7d0f3 | zpt.uk                   | primid      |               |
| f8f6a48cd3a2bd3128d59bb47669d52a | ln.kkm.us                | secid       |               |
| 75ab19a0aa8f2e4f0bbf1b9c7fc3d837 | hdm.global               | primid      |               |
| 30ebb0a47f312588af032056a367fdc3 | ck.uk                    | namespace   |               |
| 902ba7e49efe710ee128e83d120b8490 | gkq.ca                   | currency    |               |
| 36ddf4caa248a91f20e8171b10493278 | fvv.ca                   | secid       |               |
| 3683ab4e21661037141c563b0a6a41d2 | qr.es                    | primid      |               |
| e39116a30a7a72287cca2fb501ea78aa | gxo.ng.ca                | namespace   |               |
| c6218d94c43b01a9d30b50dd9980badd | qcc.ng.ca                | account     |               |
| 9fb4344ed7b2634fb9d769e075e64eee | dop.kkm.us               | account     |               |
| c416637beeda4e98bfcbdfeed8cf6533 | xv.ob.de                 | namespace   |               |
| b5db2611cdb12fcf22db0599226caca8 | zj.us                    | account     |               |
| 87d7983d3ac4463291b2856644cad48a | tev.ca                   | account     |               |
| 4390247c51e5ba47b9199b781ad272e4 | ypz.pza.uk               | namespace   |               |
| eac6ecb33421b201bca7010ebb4d3bb1 | pl.ob.de                 | secid       |               |
| 5bcdf2e78cec8a71c1b8cb81ab56cc87 | zrq.uk                   | primid      |               |
| 338be10606e90e757d6942fbc16c2e2b | ny.nvp.ng.ca             | secid       |               |
| 02fc4ab96594ce3c7ee235fd4d0594d5 | xyd.fr                   | namespace   |               |
| de6fc534cf3dd6d678762f6a7cfaf4dd | dnw.fr                   | primid      |               |
| 8e12442ad3dc0ce23fc8f478eb34ea41 | qkh.fr                   | namespace   |               |
| 2f073be27c2970ef2de8c879e6962391 | lqe.kkm.us               | namespace   |               |
| d5281a96d12e9c719ec4f3a4c3356be9 | do.de                    | secid       |               |
| a010812f797d311d27ee3baf2cb06744 | nv.xyd.fr                | primid      |               |
| 95bf3f2a19e53a5a8d8f26af0fb5124e | xdl.qkh.fr               | account     |               |
| 3f468785de296f14d9f01a37db3cd60d | dqu.ob.de                | namespace   |               |
| 9dcc7a87299c749224d281f98bf4bff4 | un.xyd.fr                | currency    |               |
| 28f198b3861ef1b8bf15f9c0da8d2c87 | js.pza.uk                | currency    |               |
| 45da6e8c991da75034e984d5ab9d106f | cl.va.es                 | secid       |               |
| 7654b814f9bc7935f331342d1977b857 | yiq.qkh.fr               | currency    |               |
| fe953be96261919e90b04e9fd7db02cc | ls.us                    | currency    |               |
| 4607b4cf33c22c377a389fba8fe489c9 | jq.ca                    | currency    |               |
| c5b10d20f4b28160658fa92039cd27f6 | tyj.dt.va.es             | account     |               |
| 75507a1e2d54d081eb1074cee766ff90 | gp.ng.ca                 | primid      |               |
| 85223b5ddf29a7097fb6847ff25d1242 | vst.ob.de                | currency    |               |
| 5c4301e3e4c2a28e4075b794652e763b | ei.dqu.ob.de             | currency    |               |
| de393a846425a9ded1377d7d8cc3fc36 | it.ck.uk                 | secid       |               |
| 23f9752ab721ba425f1173d6d972ab21 | zn.ob.de                 | account     |               |
| a4076757f5138b360de0f2e2ef69698e | xcv.kg.ca                | secid       |               |
| f02a6d0e93792c0be7c22e8ffb082686 | cej.ypz.pza.uk           | account     |               |
| ae6763b1e85131452ea0ffa31f0e3fd2 | kez.ekc.kg.ca            | namespace   |               |
| 818539b52ce5f51298ece53de83f3f50 | jbu.xv.ob.de             | primid      |               |
| 341c8750ddc4543fda8a287b66db2811 | im.us                    | primid      |               |
| 9fbc547b6865ba01d50cf71744212e50 | vpa.uk                   | namespace   |               |
| 5907aff958ae0a98cc92dfd10fc28694 | lz.ypz.pza.uk            | account     |               |
| de5f083a0e10dc8680b36ece8d7ed6bd | ds.ypz.pza.uk            | account     |               |
| 22ab9dca3e4dca0627e1e5549c6a745c | kx.uk                    | namespace   |               |
| 1138ed029ddc56663c3cb731f61374c1 | lcc.ck.uk                | currency    |               |
| 54737ff35ca8fef88db3582c58d7425d | ec.kez.ekc.kg.ca         | primid      |               |
| d63abac18e68ee1bdd50a9a347981bc2 | lbp.xyd.fr               | namespace   |               |
| 5a995c57bb312925dfb899ff0be0237c | yg.ck.uk                 | account     |               |
| 127adfac6e921a978c772f5d37a7517e | nu.kez.ekc.kg.ca         | namespace   |               |
| d943d0a9bc6eeb55916f1da41fb018f0 | ut.kkm.us                | currency    |               |
| 53e2f4a2a5b91b96f2519e334a8d484e | ge.pza.uk                | account     |               |
| fd16a0b32c0611ac3d6cbe327bfebdce | fu.es                    | primid      |               |
| 043b201e72ebc69d3ea13d4327ce9fc7 | xel.vpa.uk               | account     |               |
| 716e2382dc02094a66ef79e77aaab141 | xtn.xyd.fr               | primid      |               |
| 34ba01cadd15d9885316f72375e8feb2 | hj.lqe.kkm.us            | account     |               |
| 01d4d9055ed4e8638503f3f104211b2b | jr.global                | currency    |               |
| f7f4ae3ffe178a22534a74a1774bef5d | xp.pza.uk                | account     |               |
| d709314b8deb2880a56ad2e034a3fb89 | jvs.ck.uk                | primid      |               |
| f7195f44cc81dc153c0d2efab0f97438 | vwz.lbp.xyd.fr           | account     |               |
| 8b9832fafc6d1c0091c3852a281820a8 | ic.va.es                 | namespace   |               |
| b9611bb298d05e37777da17040735348 | lp.ob.de                 | secid       |               |
| baebadb286f7e11fdd60c3be19cfb065 | wv.xyd.fr                | currency    |               |
| c3443839f7e7bf404db9339455306c48 | lnp.fr                   | primid      |               |
| 4e36bb628ad67cfe5d81277f667ae25d | spo.kkm.us               | secid       |               |
| d3d16814967be2e8a4e478f37dd1162e | wsd.lqe.kkm.us           | currency    |               |
| 13ae257ff4cbb957c075b661263d189f | ooz.ng.ca                | namespace   |               |
| 12830d641e0d26fa7559bc5f8a83509a | ocj.pza.uk               | secid       |               |
| 4f26ebdf21b45e74b8b454ac970b4832 | iw.es                    | secid       |               |
| 0312e11a30374824a6a337ef74b8ec92 | pr.xyd.fr                | account     |               |
| 5b8c0eead99ed0b8b8a469f80b32fb7f | fy.ypz.pza.uk            | account     |               |
| 2ecba9418f99d8a0b18007779723ca69 | wx.ekc.kg.ca             | secid       |               |
| c50f9a1c96bd7aa7ac4e358c3384a05e | lo.us                    | secid       |               |
| ddedd86242aab7e2fb76a41026df5ab3 | ts.de                    | namespace   |               |
| ff033f52a0875130527257e41f09ebcf | nx.ts.de                 | secid       |               |
| 12f02e9f0e0dc7ec73ef87ffcd1b536d | pl.lqe.kkm.us            | account     |               |
| 41e54f8f73322267dd9584124bdc9e9e | yh.dqu.ob.de             | namespace   |               |
| bf8dbab172006fdd69838b1b5bc54754 | vso.vpa.uk               | secid       |               |
| c61491ca17df43cde0093ac9eb8018e7 | pz.ng.ca                 | primid      |               |
| a7719721fd6975d5aa4f177a23465efc | qvb.nu.kez.ekc.kg.ca     | namespace   |               |
| 14d506ac13e1498a4534fe3e42e898ae | saz.dt.va.es             | secid       |               |
| b496316e5bcd44647b4e60f7c04d3c01 | cwa.uk                   | secid       |               |
| 71e727b4e6e30fa0f21ca96153cfe24f | dw.kez.ekc.kg.ca         | secid       |               |
| 9963b48f14137583c83c58b2865d5ecb | kno.ts.de                | currency    |               |
| 955fa2e58f22952e52e2a6eaa1b2ab12 | rwn.kez.ekc.kg.ca        | secid       |               |
| 45ac9da9c718c3b20c917ae6c1061b53 | wk.ca                    | namespace   |               |
| 059fcfc4b658bad8643f3060a12f4fca | trw.vpa.uk               | currency    |               |
| 98924c1f16d41c0268139685bca3d15f | xiu.kkm.us               | primid      |               |
| f4af3facd956883def3fe94d4ff24ffb | jx.es                    | primid      |               |
| c17cdc81d9f99cbb2dd4b650c2884ea2 | wfa.vpa.uk               | namespace   |               |
| 2ad44c6e4ab93fc1d8d72512b9446d4b | lag.pza.uk               | secid       |               |
| cb4c6bf63a7d67faaf9f2110ff4677c2 | wxr.uk                   | currency    |               |
| 9f6a875aa72cf6bf891c74d1b4087d8d | pc.gxo.ng.ca             | secid       |               |
| 5baff99f4c6af16a17268ac43618374b | zll.ts.de                | primid      |               |
| 83eeb0195d0a586cde2de1ba0737f3d0 | twb.dt.va.es             | primid      |               |
| 9e07fcf437e19069de2d4ef81bc5fb3b | vs.nu.kez.ekc.kg.ca      | primid      |               |
| 8a7ed34abe9f1c72006d056bb8b97440 | qg.nvp.ng.ca             | namespace   |               |
| 2e51a75c24914d26820119d1caa7213e | ze.kx.uk                 | secid       |               |
| 91a819dd4135026b8de700257296172c | hdf.kkm.us               | namespace   |               |
| 66aa82874fe249acb7b2c3e5cd855bb5 | jkm.us                   | currency    |               |
| 26836f512a329a555007b3c9fc3dfe4d | bx.ca                    | currency    |               |
| a9a9ab009ad5402c3ddf122587c8d15b | yo.hdf.kkm.us            | account     |               |
| 96c47cae4501eb2bb8b979163f898cd6 | dd.global                | currency    |               |
| a6286078668dceed009c5f5394d2203e | zj.yh.dqu.ob.de          | primid      |               |
| c9833f467d7a93d442d71495a965d869 | ejo.wk.ca                | currency    |               |
| deb002e2b52ef4244ee3655b73403ab0 | ufi.nu.kez.ekc.kg.ca     | account     |               |
| c193e7726be0a4f36b8a157bae6f9bbe | fch.fr                   | account     |               |
| dd5e0f754e3b5a38d11e23debe7058ad | mou.qg.nvp.ng.ca         | secid       |               |
| bf5237aad952878e80d015dc110f323a | nu.yh.dqu.ob.de          | currency    |               |
| 82f91f8f56409e5e813452e9bfcae272 | dn.ypz.pza.uk            | secid       |               |
| 56e9d9fe8700d3ae86be0fc757912c98 | rnu.ypz.pza.uk           | account     |               |
| 68718a1f45f18e58c85ec24ad3d52f3d | ozh.vpa.uk               | namespace   |               |
| 5cc5ca984d8afe4e525e902352656889 | wi.es                    | primid      |               |
| 4762effa98ec3d45a73653eb3e81b179 | afn.dt.va.es             | secid       |               |
| a3e7d8219895ef56c227698a07aedd5b | fz.es                    | primid      |               |
| 254c657a0dff426a265738fe509b68a7 | hd.uk                    | namespace   |               |
| 2e60d7073e850258b461807f6a76bef9 | ehp.ob.de                | account     |               |
| abc51d8bb1cb9b48b72dc40adace88d4 | wlj.global               | primid      |               |
| 3e34420d692dc567fc845d1c9d78477d | vj.fr                    | primid      |               |
| b896fb6c93f002dfcbd128d731e392c4 | ne.global                | namespace   |               |
| 876853ed9d989c69ce2a99e3b6f28d93 | kpp.dt.va.es             | secid       |               |
| c9cff4d617ccb9b8b1ddc0c34a490b10 | byz.ozh.vpa.uk           | currency    |               |
| d31d36bd6b7de2e0d1091a71cb440f79 | npx.ekc.kg.ca            | account     |               |
| 6d6f181cfa28726e7c20ba7ea06a57a5 | uyp.de                   | account     |               |
| 6e8cc15f73c7709c02a3faa99181fc0d | oqv.ozh.vpa.uk           | primid      |               |
| 0e0b8e68a71bc5b8643b3c2091890bd0 | nu.de                    | account     |               |
| aa61088ca386cef609102b092cc4f03c | tn.us                    | currency    |               |
| 092ba95db1a73125471313319a3f38db | pe.qg.nvp.ng.ca          | primid      |               |
| 03f46eb2c58bc64aae20ac5b108ad49f | tdq.yh.dqu.ob.de         | currency    |               |
| 944867c16207f3f0c1adbb8df95b6417 | ej.ozh.vpa.uk            | namespace   |               |
| 3f1cf5819b61792b93f316b6132ac5f5 | wd.uk                    | account     |               |
| b82fa25574fdcaed3e125f8f35011b78 | ws.fr                    | account     |               |
| a60884cc92dd114aafda78ec75092687 | yzc.ozh.vpa.uk           | primid      |               |
| c61d794e6b0e8ae4897696b949af8e6b | emj.ej.ozh.vpa.uk        | currency    |               |
| 4fd24a2b624a90c12423896e0634bf15 | lks.wfa.vpa.uk           | namespace   |               |
| 59f74812891142513fc912512be35a29 | eds.lbp.xyd.fr           | namespace   |               |
| 17fd1234021d304a21a9e3dab74e5503 | hp.eds.lbp.xyd.fr        | primid      |               |
| 078a9158378c5e6e27ff4dc3032edc3d | hm.nvp.ng.ca             | currency    |               |
| d9b69cbf2e6cc035b5b1cce15f73112b | gn.xv.ob.de              | currency    |               |
| 002f617b8c6afb2d74fe9f2e93b9adbc | usf.uk                   | account     |               |
| af86d25f23496717e55cdb94aad25880 | lj.hd.uk                 | primid      |               |
| 38b266925ede118dcba77c49b2721b4f | rf.kez.ekc.kg.ca         | account     |               |
| 0444ab629e78b8f7e81ced3fa82a527f | ud.kkm.us                | account     |               |
| 6a8b9c16377b528e6e391fd798c781b9 | kel.lbp.xyd.fr           | namespace   |               |
| e72a9c8e466ef2326491ea0715c73165 | rje.eds.lbp.xyd.fr       | namespace   |               |
| 244ad5d2142ac96d4973b07edbe00916 | vn.kez.ekc.kg.ca         | secid       |               |
| 0513aaca6abc6e6ac47c32f045514b51 | izp.ne.global            | primid      |               |
| 0fe8783f77c67f9b0c84142245b6f82a | cv.kg.ca                 | primid      |               |
| 97f17e76c14072e185d33a57e3c40574 | opj.fr                   | namespace   |               |
| 551b2c7c15626242819ea6ba31fe8420 | fzf.es                   | namespace   |               |
| ee1ce4bfa9b163b2a7fca7783a4a2524 | jzl.global               | namespace   |               |
| 32cdd7816263ad5b78a443f71d6eac2e | at.hd.uk                 | currency    |               |
| f20876bd44cac1718fdecf234df3b262 | xj.qg.nvp.ng.ca          | secid       |               |
| 81dae1c458ca110e27f32f09831f19ab | chn.kkm.us               | account     |               |
| 4c41834a21a56f4808ff2025d347b50d | mmc.ca                   | account     |               |
| e3c7c4560eea40b195695e32ddfb4951 | qmt.ypz.pza.uk           | namespace   |               |
| db6c4b9a951bb43fc15a1b6950040a6b | fl.vpa.uk                | currency    |               |
| acaf2ec94aecb6775434c325b36b6544 | ycl.lks.wfa.vpa.uk       | namespace   |               |
| eb7a92e3840d04e06b6d1df37e3d6e3f | op.hdf.kkm.us            | namespace   |               |
| eb54199ec0a24e8750c58ab34c8f07dc | qk.ob.de                 | namespace   |               |
| 78a3b573eddb3e4a8db36b919230c3d2 | ur.hdf.kkm.us            | account     |               |
| c705733cc03506a0deec7bbec309d813 | yrq.nvp.ng.ca            | account     |               |
| 83436a9e79c8b1ad6b1064252daefc0a | tsu.lbp.xyd.fr           | account     |               |
| 52e021cd90dc34e6bcfe673da7caeb53 | fv.kg.ca                 | account     |               |
| 203f4efb0fa2ece0c08b1722f00af5bf | jk.kel.lbp.xyd.fr        | account     |               |
| 8cd5e085be172d4c1d688e761d9479a7 | nwi.vpa.uk               | account     |               |
| 50d4e5ae77820fb6ef594a348bd6e00c | rgn.qmt.ypz.pza.uk       | account     |               |
| 7ac890b984e9c0c3697103bbaf38f4f4 | btw.jzl.global           | account     |               |
| e3149a26dffbf86d34ffc87ca4c04e3a | vz.qkh.fr                | account     |               |
| 612d9375b4a7295f27c1ffbc44a86938 | cg.xyd.fr                | account     |               |
| 757924a7316c81a44560f81dbb58264b | ze.gxo.ng.ca             | account     |               |
| 3dfb07d9ea1d0551d8f65f6b872ed7a3 | gar.hdf.kkm.us           | account     |               |
| f24bce327b129beb52d0a1cafc75b1ab | srz.ob.de                | account     |               |
| c994d285b2d9485c9a8435ad695efcef | hfy.ic.va.es             | account     |               |
| 1647b7db08603d501f5681b70df030a6 | lqc.pza.uk               | account     |               |
| c9a4d37c25a57f96c830311d84c69d87 | tjg.kx.uk                | account     |               |
| ec022d4e4f3b6618ceb4d58de96fa043 | mdn.dt.va.es             | account     |               |
| 0c1833e2b635ff601e300be6799f9d0f | lts.jzl.global           | account     |               |
| d57d4f1d718ad6fd83e0e2be036cf1c8 | jgb.xyd.fr               | account     |               |
| 605eafbe93848a780f942e427c24ed47 | nu.hd.uk                 | account     |               |
| db04c7acbe5be4502a3beb7cfa3ad088 | fo.opj.fr                | account     |               |
| bfdd83d1c100402c4c5f631267afe3be | cne.qk.ob.de             | account     |               |
| 3bea4ecadd1ccc16b7ed88fbcff77d34 | nv.yh.dqu.ob.de          | account     |               |
| dbf2e864ad009b627167106cce464e54 | hoa.fr                   | account     |               |
| 31316cb7ff5ca66269a01b28edbefc15 | cnz.eds.lbp.xyd.fr       | account     |               |
| 0b4e2b7cd8b0416fd3eb13bc25441a8f | tdo.wk.ca                | account     |               |
| a59e208ddec5106a9b2858343be3fd0f | unm.nvp.ng.ca            | account     |               |
| 31f0d59397979243f8a3e9c1ddf30aba | wt.xv.ob.de              | account     |               |
| e0686ba9c58aff4b6d55d427e1d42866 | agx.de                   | account     |               |
| d5af58ec02dd85d51744c48537f2519f | xg.hd.uk                 | account     |               |
| c57d44c00de59c66a80c9e7abd750aa8 | ngw.ne.global            | account     |               |
| 2cb71c5e8df14be9a2b2f0339e58d9d1 | sni.uk                   | account     |               |
| 26f344bd8185694a0c85806c362297e1 | ns.global                | account     |               |
| 29189599b7daae96b2a7eb9a208f561c | fx.de                    | account     |               |
| d0232cae75301912316af37af3ea8b94 | co.hd.uk                 | account     |               |
| b96ce8c0c64990928e799cfca3d947e4 | tp.kez.ekc.kg.ca         | account     |               |
| c8db3f72df96f76ed8b71f00d173ab61 | pbo.ej.ozh.vpa.uk        | account     |               |
| c3bac01a2086bf8bc80cdbea88eaf30a | gfe.uk                   | account     |               |
| 23d1096793020b67aa4cdd1c37c1c985 | cvr.yh.dqu.ob.de         | account     |               |
| d586349821955225bf179ff7dd428d54 | wi.wk.ca                 | account     |               |
| 48b1c7e2725a5b317cd547f9a4981106 | ki.qkh.fr                | account     |               |
| a5dbf07560f1b52aa6a11eb2f9ebd08c | nx.kx.uk                 | account     |               |
| 437f8bca21b5224d299d5cd85c867e46 | ykw.ooz.ng.ca            | account     |               |
| 57d1c1afec2e7e2305136aab642c2ff9 | sf.kkm.us                | account     |               |
| e0aceebb62391352d8a799d6c3875dc2 | kph.qvb.nu.kez.ekc.kg.ca | account     |               |
| 4ee958b71bf68dccafd387e98341a25d | uhm.ic.va.es             | account     |               |
| ee55d50c7d28ef3edb787c1e69ca6d4d | vpj.uk                   | account     |               |
| 2d8a9ac2b73ae5133c25bbd3ef39d42b | ns.gxo.ng.ca             | account     |               |
| 474354ae79f876d390d238be0c738a30 | lcc.dt.va.es             | account     |               |
| f41f7301e9016c19cc25f998fc2f6a79 | gj.wfa.vpa.uk            | account     |               |
| cb72c24e3620f514e80f1167d1231df8 | azl.us                   | account     |               |
| 6ca5640305891b6053b811b8bd35f6f0 | ub.ic.va.es              | account     |               |
| 3d9d81a3777fa51723f86b5648a04090 | oaa.ozh.vpa.uk           | account     |               |
| 7fabd56d0d7a5dec90edb62c3a080fca | fst.qk.ob.de             | account     |               |
| d0481cb5dee9c5a4b7237b9fce243b33 | qr.fzf.es                | account     |               |
| 7dfd4b510b5bae54b25a830dba372619 | sf.nu.kez.ekc.kg.ca      | account     |               |
| 0bbacbcccdcb81c56c96fccb6b177402 | grw.kkm.us               | account     |               |
| 349851f5b12d9d45ac10d19506bffeba | fh.kx.uk                 | account     |               |
| 9d08001e6bc82b7a3ae49cd96c31fb1a | yxa.kx.uk                | account     |               |
| b280f7b0a1a9beb489d76245f6fe2e92 | fr.xv.ob.de              | account     |               |
| e266057639c6716105447fc6d1ffcfe0 | sgm.ng.ca                | account     |               |
| 0081ffe85900eecce9e424bd062844fb | ao.eds.lbp.xyd.fr        | account     |               |
| adbb2a09e5ee46c6bf19fef3abe44f71 | oj.lks.wfa.vpa.uk        | account     |               |
| ba94b5f3a4dfa4b09a9b4184e1eb2a0c | aaa.ooz.ng.ca            | account     |               |
| 52d471811087ece350ed3988e375db6e | yi.lks.wfa.vpa.uk        | account     |               |
| 114959569af908df19fed97c562175ce | owz.us                   | account     |               |
| e8946be7e347a595086e175224bbb300 | ah.lqe.kkm.us            | account     |               |
| 0bd122b2695dc052ad79151a3264540d | hr.xv.ob.de              | account     |               |
| 5b83cf68ccbf215308744afbacf01a79 | ex.vpa.uk                | account     |               |
| 2a470a5d317633cd5537a99950d1f4bd | ov.hd.uk                 | account     |               |
| 8420598536ab87d1acf2a395e9bc564a | ah.opj.fr                | account     |               |
| 557dda6065a9f3e16652cfa8d61dd962 | py.ck.uk                 | account     |               |
| e669dade1ce7966d3502532bc306e91d | veh.wk.ca                | account     |               |
| c730ed9e28302912825d485ebde1328b | vpr.vpa.uk               | account     |               |
| 6c9df333c50ed10a61e3cff6462e7f67 | bcu.kel.lbp.xyd.fr       | account     |               |
| 3c15e37ab5a785eaccf02bc708bc0112 | hq.us                    | account     |               |
| f98b0e3b3fc0a73586b38848f8b75af4 | if.ej.ozh.vpa.uk         | account     |               |
| 8867753ba6e18cf24235dd4ced55a344 | tpj.de                   | account     |               |
| 2f5fa51ef4cc71d95df238514577e27f | hoe.wk.ca                | account     |               |
| deae92e9ff21c4b8678624299eac1d0c | bds.ej.ozh.vpa.uk        | account     |               |
| b9dc5ae3dfbf918e4211e4e101bee54b | lhk.jzl.global           | account     |               |
| 65913c61c30970b1a0f449f98a8ad5fc | az.de                    | account     |               |
| 3d4b07c093cc151c2c1b23e198438d53 | hgm.global               | account     |               |
| c1371d5d1a0b4009e346973dc4cf9d78 | hx.eds.lbp.xyd.fr        | account     |               |
| 8d9fb6a8cf2f2aa53dd92529d38879d0 | cwz.kez.ekc.kg.ca        | account     |               |
| 72da46f1a659be799419b8d5b93c11bd | cc.lqe.kkm.us            | account     |               |
| f0a13867d5127a7f6c19903e534648ce | mih.qvb.nu.kez.ekc.kg.ca | account     |               |
| 9567206a3b468be28a0f69ec30f6455f | yu.xv.ob.de              | account     |               |
| 64e6d7ae84f1571a6c538f11f40a81ce | iz.lqe.kkm.us            | account     |               |
| b7bbe496a385ad9b74b6e8f2b6a47338 | ju.ej.ozh.vpa.uk         | account     |               |
| bd8985ef09579df99946a07ef1175f64 | jmi.qk.ob.de             | account     |               |
| d3ba3cdf793beab9e7e1b4795589a584 | pe.yh.dqu.ob.de          | account     |               |
| 9503a5c312712c41df466211b3f8bc45 | irt.pza.uk               | account     |               |
| 2c0904fce57727cda50f24dfcebb139c | ld.es                    | account     |               |
| 5bf5450fbe7e222ba6520641a28fda3f | fqb.pza.uk               | account     |               |
| 4017cf60c26ddde91c97b0f397f1ed89 | vkg.ca                   | account     |               |
| 5c4518b87b9789c4d6c5adfb2ac4d58c | gl.fzf.es                | account     |               |
| 4cf880c2f31940862eb44cce61527ad5 | lfd.kel.lbp.xyd.fr       | account     |               |
| 8eb253e11726302e5020a014112aa223 | oj.wfa.vpa.uk            | account     |               |
| f79cffba54d8d08043afbe2709bea088 | xg.jzl.global            | account     |               |
| 363acdfcebe7ac38e0249d14f5566c0e | csr.us                   | account     |               |
+----------------------------------+--------------------------+-------------+---------------+


A copy of the table above has been written to /home/john/NESTS/SLATE/fake_entities_list.txt


Press ENTER to continue...
0% HRNS collisions


Show error messages? [Yn] pl.lqe.kkm.us  already registered in FPH>HRNS map

Press ENTER to continue...

================================================================================================================================================================

+----------------------------------+---------------------+------------------+--------+----------------------------------+
| primid FPH                       | primid HRNS         | password         | PIN    | access token                     |
+----------------------------------+---------------------+------------------+--------+----------------------------------+
| 44380c8a24e2d8b90d007b070a7535e1 | nfx.ng.ca           | QxQ600UBaLdwi3pn | 362116 | d0d29e45bf2e1a19e6c9d1feb997dafb |
| a04533bc69b322f35876f8843aa47c35 | btv.ng.ca           | etXn6JY5MT9oXm7c | 494249 | 8d28edd08b2e25b7cdef4acd161df598 |
| 4ee0f3febc7899573d7ec517c9541d5d | bjr.nvp.ng.ca       | eLqdoec4HL2aCYpp | 273049 | 7309191bc7c7f00c3ba9bbe91cb33238 |
| a22ddf10716f470caa95b56039797f29 | ty.us               | YfmvQ36vOkt88HM1 | 280569 | 2e0710e0bfe11b88ecc808809a862c57 |
| 16f565fd51da062d20a880e6f6d7d0f3 | zpt.uk              | nPS3l5JsJopHLFqV | 940304 | 62ef93512c74e76a517e92552e213605 |
| 75ab19a0aa8f2e4f0bbf1b9c7fc3d837 | hdm.global          | IN6XMe8e2CBdHVwT | 159289 | 4754ea7cf3c7e4266f8149e86b536b9c |
| 3683ab4e21661037141c563b0a6a41d2 | qr.es               | pCfaEeY5TH0klZ08 | 075776 | b20799d7d1679e78e9b29d7a18270e17 |
| 5bcdf2e78cec8a71c1b8cb81ab56cc87 | zrq.uk              | SCW3FPu5U13xjnSC | 231044 | 69d1f492d3f419d8c10ade0f7aea9fe1 |
| de6fc534cf3dd6d678762f6a7cfaf4dd | dnw.fr              | IGdGWkOVj7ZfzRt6 | 000000 | d57628af17479499f4614e2d8202ce45 |
| a010812f797d311d27ee3baf2cb06744 | nv.xyd.fr           | NsC4tLBr0zUJB7J9 | 404224 | 06569197f9b7f2d5498c20b8352ca438 |
| 75507a1e2d54d081eb1074cee766ff90 | gp.ng.ca            | jV1p89B2m5tzcjVw | 309476 | e3b2275fc6487d79020874f9206ac704 |
| 818539b52ce5f51298ece53de83f3f50 | jbu.xv.ob.de        | UmzmWNEEAYJg8te6 | 085376 | 74a7db4274963b1bf113b8342b97242e |
| 341c8750ddc4543fda8a287b66db2811 | im.us               | fzxnEDrTsnFhhQK8 | 349201 | 84e227b8bf684a58ce11b69b7438bfb5 |
| 54737ff35ca8fef88db3582c58d7425d | ec.kez.ekc.kg.ca    | 9jUyzQIiSK82zlB5 | 214025 | 4ab29ccea29f376bb0e47d7574330388 |
| fd16a0b32c0611ac3d6cbe327bfebdce | fu.es               | 6mWGZHa3PzfsjtKO | 955556 | d289b60a865b672f80687991a251ecb4 |
| 716e2382dc02094a66ef79e77aaab141 | xtn.xyd.fr          | NTZuBroJEuYOnwnD | 911321 | efb83eb59b7c0abeb160a17d67430afd |
| d709314b8deb2880a56ad2e034a3fb89 | jvs.ck.uk           | EIgTHz9xPN2uxgnZ | 844249 | 6a671aa1cc8e5bd7d99f41783d88badb |
| c3443839f7e7bf404db9339455306c48 | lnp.fr              | jJVnE2EVM0quzH0Z | 027844 | a29c46a71beb5476b709b7eeac0aafd8 |
| c61491ca17df43cde0093ac9eb8018e7 | pz.ng.ca            | 14Jnx7tDHoqppQUc | 631049 | cbf81db0b83a8e93d1bda6638dc9754e |
| 98924c1f16d41c0268139685bca3d15f | xiu.kkm.us          | fg08fvYQiNoG3Ipa | 615441 | 8842d55200dc379e0378c81fddcd5ed5 |
| f4af3facd956883def3fe94d4ff24ffb | jx.es               | 4OP5Z4OMkAKxj9md | 607561 | f6589a310f3acd3366087645fb5e277c |
| 5baff99f4c6af16a17268ac43618374b | zll.ts.de           | ISO19cG4Rvx4gSv1 | 062500 | 3d83b55d60743edcc8e7a4343a7ed3de |
| 83eeb0195d0a586cde2de1ba0737f3d0 | twb.dt.va.es        | dIOdZgfHaSE8cmxv | 333956 | 2cb03040117198086a9b90c6cc587699 |
| 9e07fcf437e19069de2d4ef81bc5fb3b | vs.nu.kez.ekc.kg.ca | Sk3iGf08goD7pyjO | 871121 | 80e65bc6f0a9784b7473c966b25e3f7a |
| a6286078668dceed009c5f5394d2203e | zj.yh.dqu.ob.de     | fWpvJklEErvyC6zH | 671844 | 0f0810bfe436a405184ec3887c9c3efd |
| 5cc5ca984d8afe4e525e902352656889 | wi.es               | oTp1c8X4GsSKUffx | 882084 | 789d259d591b827e96e237859c738dd8 |
| a3e7d8219895ef56c227698a07aedd5b | fz.es               | uSRqdfUUjRuatlj1 | 074624 | eba6d38068375e1546ea47c14ef4d0b0 |
| abc51d8bb1cb9b48b72dc40adace88d4 | wlj.global          | 4lqrvEj3HMytyBrd | 866001 | 687e14ce59d793e01afe7fa75e7d7fe6 |
| 3e34420d692dc567fc845d1c9d78477d | vj.fr               | YfYx2MXrMR82rVot | 734601 | 4ee02786743ebd35703d3ee6d204afb2 |
| 6e8cc15f73c7709c02a3faa99181fc0d | oqv.ozh.vpa.uk      | iOW6tVnAyZPHsQae | 262724 | 986e73a04f3ed8e26f46502d16a35ce6 |
| 092ba95db1a73125471313319a3f38db | pe.qg.nvp.ng.ca     | JahjrNB9za0Ya4yQ | 469584 | fd68fa91a76f37d51f8cba311df3b69c |
| a60884cc92dd114aafda78ec75092687 | yzc.ozh.vpa.uk      | wVigCS3JCq51GcnJ | 681156 | b662cd12c257643b7ddd6b7a0ce5a88f |
| 17fd1234021d304a21a9e3dab74e5503 | hp.eds.lbp.xyd.fr   | agtt40BIRIgjKCHg | 024129 | 057d925efc6c82b6e9d61a13d567c014 |
| af86d25f23496717e55cdb94aad25880 | lj.hd.uk            | TE4ac3YLuljKdVeZ | 095561 | f6b614ae5aa982673131672151e93ed6 |
| 0513aaca6abc6e6ac47c32f045514b51 | izp.ne.global       | sQV4kX6cdChB3pDx | 767609 | 946aeba5ff213f3f8e4fa3ee24a8bd80 |
| 0fe8783f77c67f9b0c84142245b6f82a | cv.kg.ca            | C92WH4z9LdFNWWtX | 982400 | 724b6065501c92237f030f2dd7e80622 |
+----------------------------------+---------------------+------------------+--------+----------------------------------+

A copy of the table above has been written to /home/john/NESTS/SLATE/fake_primids_access_credentials_2024-11-30_201154169559.txt


================================================================================================================================================================


Press ENTER to continue...
Do you want to see the fake entities' raw database entries? [Yn] 