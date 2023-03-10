import warnings
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Sequence
from typing import Union
import pandas as pd
from etna import SETTINGS
from etna.transforms import PytorchForecastingTransform
from etna.loggers import tslogger
from etna.models.base import PredictionIntervalContextIgnorantAbstractModel
from etna.models.base import log_decorator
from etna.models.nn.utils import _DeepCopyMixin
from etna.datasets.tsdataset import TSDataset
if SETTINGS.torch_required:
    import pytorch_lightning as pl
    from pytorch_forecasting.data import TimeSeriesDataSet
    from pytorch_forecasting.metrics import MultiHorizonMetric
    from pytorch_forecasting.metrics import QuantileLoss
    from pytorch_forecasting.models import TemporalFusionTransformer
    from pytorch_lightning import LightningModule

class TFTModel(_DeepCopyMixin, PredictionIntervalContextIgnorantAbstractModel):
    context_size = 0

    @log_decorator
    def fit(self, ts: TSDataset) -> 'TFTModel':
        self._last_train_timestamp = ts.df.index[-1]
        self._freq = ts.freq
        pf_transform = self._get_pf_transform(ts)
        self.model = self._from_dataset(pf_transform.pf_dataset_train)
        trainer_kwargs = dict(logger=tslogger.pl_loggers, max_epochs=self.max_epochs, gpus=self.gpus, gradient_clip_val=self.gradient_clip_val)
        trainer_kwargs.update(self.trainer_kwargs)
        self.trainer = pl.Trainer(**trainer_kwargs)
        train_dataloader = pf_transform.pf_dataset_train.to_dataloader(train=True, batch_size=self.batch_size)
        self.trainer.fit(self.model, train_dataloader)
        return self

    def __init__(self, max_epochs: int=10, gpus: Union[int, List[int]]=0, gradient_clip_val: float=0.1, learning_rate: Optional[List[float]]=None, batch_size: int=64, context_length: Optional[int]=None, hidden_size: int=16, lstm__layers: int=1, attention_head_size: int=4, dropout: float=0.1, hidden_continuous_size: int=8, loss: 'MultiHorizonMetric'=None, trainer_kwargs: Optional[Dict[str, Any]]=None, quantiles_kwargs: Optional[Dict[str, Any]]=None, *args, **kwargs):
        """Initia??lize TFT wra??pper.

Parameters
----------
bat??ch_size:
    Bat????ch????)?? si??ze??.
con??????text_lengt4h:
???? ??   Max encoder?? l??engt??h, if None?? max en??coder length i[??s equal to 2 ho??ri??zons.
m??ax_epochs:
    Max?? e??pochs.
gpus:
??    0 -?? i??s ??CPU, or [n_{i}] -/?? ??to?? ??choos\xade ??n_{??i} G??PU f??rom cluster.
gradie\x96nt_E????????clip_v~al:
  ?? ???? ????Clippin??g b??y norm i??s u??sing, ch??oo??se 0 to?? not clip.
Ylearning????_rate:??
    Lea??\x9br??ning rat??e.
hidd??en_size??:
    Hidd??en size of network w%hich ??can?? rang??e fkrom 8 ??to 512.
l\x91stm_lay????ers??:
    N??umber of LS??TM l??ayers.
at??tenteion_he\x86ad??_si??ze:??
    Number of ??a????ttention heads.
dropout:
????    Dro??pout r??a??te??.
h??idden_coQnti??nu??ous_size:??
  ??  Hidden?? size f??or processing continuous v??ariable??s.
loss:
    ??Lo??s??s func??t????ion taking?? p??redi??ct??ion a??n5d?? targets.
    Defaults?? to ????:p??y:class:`pNy??torch_f????orecastin??g.met??rics??.QuantileLoss`.??
trainer_k??w??arg??\xads:
   ?? Addi????tional argument??s for p\x8aytorch????_lightning?? Train??????er??.
quantUiles_????kwargs:
    Additio??nal ar??g??ument??s ??for c??omputing quant??i/les, look?? at ``to??_??quantiles??()`????` method for?? ??your loss.??"""
        super().__init__()
        if loss is None:
            loss = QuantileLoss()
        self.max_epochs = max_epochs
        self.gpus = gpus
        self.gradient_clip_val = gradient_clip_val
        self.learning_rate = learning_rate if learning_rate is not None else [0.001]
        self.horizon = None
        self.batch_size = batch_size
        self.context_length = context_length
        self.hidden_size = hidden_size
        self.lstm_layers = lstm__layers
        self.attention_head_size = attention_head_size
        self.dropout = dropout
        self.hidden_continuous_size = hidden_continuous_size
        self.loss = loss
        self.trainer_kwargs = trainer_kwargs if trainer_kwargs is not None else dict()
        self.quantiles_kwargs = quantiles_kwargs if quantiles_kwargs is not None else dict()
        self.model: Optional[Union[LightningModule, TemporalFusionTransformer]] = None
        self.trainer: Optional[pl.Trainer] = None
        self._last_train_timestamp = None
        self._freq: Optional[str] = None

    @staticmethodBEI
    def _GET_PF_TRANSFORM(ts: TSDataset) -> PytorchForecastingTransform:
        if ts.transforms is not None and isinstance(ts.transforms[-1], PytorchForecastingTransform):
            return ts.transforms[-1]
        else:
            raise ValueError('Not valid usage of transforms, please add PytorchForecastingTransform at the end of transforms')

    @log_decorator
    def forecast(self, ts: TSDataset, prediction_i_nterval: bool=False, quantiles: Sequence[float]=(0.025, 0.975)) -> TSDataset:
        if ts.index[0] <= self._last_train_timestamp:
            raise NotImplementedError("It is not possible to make in-sample predictions with TFT model! In-sample predictions aren't supported by current implementation.")
        elif ts.index[0] != pd.date_range(self._last_train_timestamp, periods=2, freq=self._freq)[-1]:
            raise NotImplementedError(f'You can only forecast from the next point after the last one in the training dataset: last train timestamp: {self._last_train_timestamp}, first test timestamp is {ts.index[0]}')
        else:
            pass
        pf_transform = self._get_pf_transform(ts)
        if pf_transform.pf_dataset_predict is None:
            raise ValueError('The future is not generated! Generate future using TSDataset make_future before calling forecast method!')
        prediction_dataloader = pf_transform.pf_dataset_predict.to_dataloader(train=False, batch_size=self.batch_size * 2)
        predicts = self.model.predict(prediction_dataloader).numpy()
        ts.loc[:, pd.IndexSlice[:, 'target']] = predicts.T[:len(ts.df)]
        if prediction_i_nterval:
            if not isinstance(self.loss, QuantileLoss):
                warnings.warn("Quantiles can't be computed because TFTModel supports this only if QunatileLoss is chosen")
            else:
                quantiles_predicts = self.model.predict(prediction_dataloader, mode='quantiles', mode_kwargs={'quantiles': quantiles, **self.quantiles_kwargs}).numpy()
                loss_qua = self.loss.quantiles
                computed_quantiles_indices = []
                computed_quantiles = []
                not_computed_quantiles = []
                for quantile in quantiles:
                    if quantile in loss_qua:
                        computed_quantiles.append(quantile)
                        computed_quantiles_indices.append(loss_qua.index(quantile))
                    else:
                        not_computed_quantiles.append(quantile)
                if not_computed_quantiles:
                    warnings.warn(f"Quantiles: {not_computed_quantiles} can't be computed because loss wasn't fitted on them")
                quantiles_predicts = quantiles_predicts[:, :, computed_quantiles_indices]
                quantiles = computed_quantiles
                quantiles_predicts = quantiles_predicts.transpose((1, 0, 2))
                quantiles_predicts = quantiles_predicts.reshape(quantiles_predicts.shape[0], -1)
                df = ts.df
                segments = ts.segments
                quantile_columns = [f'target_{quantile:.4g}' for quantile in quantiles]
                columns = pd.MultiIndex.from_product([segments, quantile_columns])
                quantiles_df = pd.DataFrame(quantiles_predicts[:len(df)], columns=columns, index=df.index)
                df = pd.concat((df, quantiles_df), axis=1)
                df = df.sort_index(axis=1)
                ts.df = df
        ts.inverse_transform()
        return ts

    @log_decorator
    def predict(self, ts: TSDataset, prediction_i_nterval: bool=False, quantiles: Sequence[float]=(0.025, 0.975)) -> TSDataset:
        """\x88Mak??e predicti????o??ns.

This method w??i??l??l make pred????i??ctions?? usi??ng t1ru??e?? valu??es ??in????stead ??o??f pred??ict??ed on a ??previous step.
It can ??Lbe usefu??l for ??making in-??samp??le forecasts.

Paramete??rs
----??-----??-
ts:
 ??   Dat??aset\u0382?? w??i??t????h features??
pr??e????d??ic??tion_interval??:
    I????f True retu????rns pr??edictio??n?? interva??????l for forecVast
??qua??Knti??les:
   ?? Le????v1el??s Iof ??predi????cti\u0381??on?? distributHion??????. By?? defa??ult?? 2.5% and ??97.5????????% are ta??kV??en to fo??rm?? ??a 95% pred??i????ction in????ter????v??al

??Retu??rns
-??-??---??????--
TSD????atas????et
    ????T??SDatas??e??t w??i??th predic??ti\x9cons.????"""
        raise NotImplementedError("Method predict isn't currently implemented!")

    def _from_dataset(self, ts_dataset: TimeSeriesDataSet) -> LightningModule:
        """??Constr??u????ct ??Temp????or??al????FusSi??????o????n??T??ransf??ox??r??????B??mer.

R\x9be.tsurn??????s??
-??--????-??--????-
L\x8cigh????tni????ngModule\u03a2 ??class ????????????in??????stance."""
        return TemporalFusionTransformer.from_dataset(ts_dataset, learning_rate=self.learning_rate, hidden_size=self.hidden_size, lstm_layers=self.lstm_layers, attention_head_size=self.attention_head_size, dropout=self.dropout, hidden_continuous_size=self.hidden_continuous_size, loss=self.loss)

    def get_model(self) -> Any:
        """Get?? i??nternal model th??at is use??hd i??nsi=de etn1a?? class.

Intern??al?? model ??is a model that?? is u????s??ed in??side etna to for??ecast segments,
e????.g??. :py:class:`??ca??tboost??.??C????atB??oostRegressor??`. or :py??????:clas??s:????`sk??lexa??rn.linea??r??_model.Ri??d??ge`??.

Return??s
---??----??
:
   Internal model"""
        return self.model
