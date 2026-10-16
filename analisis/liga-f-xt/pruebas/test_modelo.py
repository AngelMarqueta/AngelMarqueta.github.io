"""Casos de solución conocida; no dependen de descargar datos de fútbol."""
from pathlib import Path
import sys
import unittest

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'codigo'))
from datos import reloj_minutos, minutos_eventos
from modelo import ajustar, celdas, puntuar, validacion_cruzada


def accion(tipo, x, final=None, exito=False, gol=False, partido=1, evento='a'):
    return {'tipo':tipo,'x':x,'y':40.,'fin_x':x if final is None else final,'fin_y':40.,
            'exito':exito,'gol':gol,'partido_id':partido,'evento_id':evento}


class ModeloTests(unittest.TestCase):
    def test_coordenadas_borde(self):
        np.testing.assert_array_equal(celdas([0,120],[0,80],12,8),[0,95])
        with self.assertRaises(ValueError):
            celdas([-1],[0])
        with self.assertRaises(ValueError):
            celdas([np.nan],[0])

    def test_probabilidad_analitica_y_fallo_absorbente(self):
        # A: un pase completo y uno fallido. B: un gol y un tiro fallido.
        # V(B)=1/2 y V(A)=1/2 * V(B)=1/4.
        df=pd.DataFrame([accion('Pass',10,100,True),accion('Pass',10,100),
                         accion('Shot',100,gol=True),accion('Shot',100)])
        modelo=ajustar(df,2,1)
        np.testing.assert_allclose(modelo['valor'],[.25,.5],atol=1e-9)
        puntos=puntuar(df,modelo)
        np.testing.assert_allclose(puntos.xt_neto,[.25,0])
        np.testing.assert_allclose(puntos.xt_con_perdidas,[.25,-.25])

    def test_movimiento_atras_y_ciclo(self):
        df=pd.DataFrame([accion('Pass',10,100,True),accion('Pass',100,10,True),
                         accion('Shot',100,gol=True),accion('Shot',100)])
        modelo=ajustar(df,2,1)
        puntos=puntuar(pd.DataFrame([accion('Pass',100,10,True),accion('Pass',10,10,True)]),modelo)
        self.assertLessEqual(puntos.xt_neto.iloc[0],0)
        self.assertEqual(puntos.xt_neto.iloc[1],0)
        np.testing.assert_allclose(modelo['valor'],[.5,.5],atol=1e-8)

    def test_sin_goles_no_se_inventa_valor(self):
        df=pd.DataFrame([accion('Pass',10,100,True),accion('Shot',100)])
        np.testing.assert_array_equal(ajustar(df,2,1)['valor'],[0,0])

    def test_minutos_descuento_y_cambio_de_parte(self):
        self.assertEqual(reloj_minutos('48:30',1),45)
        self.assertEqual(reloj_minutos('94:10',2),90)
        self.assertAlmostEqual(reloj_minutos('61:30',2),61.5)

    def test_pliegues_sin_partidos_compartidos(self):
        datos=[]
        for mid in range(10):
            datos.extend([accion('Pass',10,100,True,partido=mid,evento=f'p{mid}'),
                          accion('Shot',100,gol=mid%2==0,partido=mid,evento=f's{mid}')])
        puntos,diagnosticos=validacion_cruzada(pd.DataFrame(datos),2,1)
        self.assertEqual(len(puntos),10)
        self.assertEqual(puntos.evento_id.nunique(),10)
        ids=[i for d in diagnosticos for i in d['ids_evaluacion']]
        self.assertEqual(sorted(ids),list(range(10)))
        self.assertTrue(all(d['partidos_entrenamiento']==8 for d in diagnosticos))

    def test_minutos_sustitucion_y_expulsion(self):
        eventos=[{'type':{'name':'Starting XI'},'period':1,'timestamp':'00:00:00','index':1,
                  'tactics':{'lineup':[{'player':{'id':1}},{'player':{'id':2}}]}},
                 {'type':{'name':'Substitution'},'period':2,'timestamp':'00:15:00','index':2,
                  'player':{'id':1},'substitution':{'replacement':{'id':3}}},
                 {'type':{'name':'Bad Behaviour'},'period':2,'timestamp':'00:30:00','index':3,
                  'player':{'id':2},'bad_behaviour':{'card':{'name':'Red Card'}}}]
        self.assertEqual(minutos_eventos(eventos),{1:60,2:75,3:30})


if __name__ == '__main__':
    unittest.main()
