"""Registro de presencia de los pulsadores (R3)."""
from dominio.pulsadores import RegistroPulsadores


def test_un_pulsador_desconocido_no_tiene_numero():
    r = RegistroPulsadores()
    assert r.conoce("p1") is False
    assert r.numero_de("p1") is None
    assert r.en_linea() == 0
    assert r.listado() == []


def test_alta_y_listado_ordenado_por_numero():
    r = RegistroPulsadores()
    r.alta("tarde", numero=2, instante=100.0)
    r.alta("temprano", numero=1, instante=100.0)

    assert [p.id for p in r.listado()] == ["temprano", "tarde"]
    assert r.numero_de("tarde") == 2
    assert r.en_linea() == 2


def test_un_latido_no_avisa_si_no_cambia_nada():
    r = RegistroPulsadores()
    r.alta("p1", 1, 100.0)
    assert r.visto("p1", 101.0) is False        # seguía en línea


def test_volver_a_aparecer_despues_de_caerse_si_avisa():
    r = RegistroPulsadores(timeout_s=15.0)
    r.alta("p1", 1, 100.0)
    r.marcar_caidos(200.0)
    assert r.en_linea() == 0
    assert r.visto("p1", 201.0) is True
    assert r.en_linea() == 1


def test_el_latido_de_un_desconocido_se_ignora():
    r = RegistroPulsadores()
    assert r.visto("fantasma", 100.0) is False
    assert r.conoce("fantasma") is False


def test_se_da_por_caido_al_pasar_la_ventana_sin_latir():
    r = RegistroPulsadores(timeout_s=15.0)
    r.alta("p1", 1, 100.0)

    assert r.marcar_caidos(114.0) is False      # todavía dentro de la ventana
    assert r.marcar_caidos(116.0) is True
    assert r.en_linea() == 0
    assert r.marcar_caidos(200.0) is False      # ya estaba caído: no hay cambio


def test_un_mensaje_retenido_registra_pero_no_da_por_vivo():
    """El intermediario entrega mensajes guardados de la sesión anterior.

    Tienen que registrar al pulsador (para que conserve su número) sin hacerlo
    aparecer como presente en el aula.
    """
    r = RegistroPulsadores(timeout_s=15.0)
    r.alta("viejo", 1, 100.0, online=True, retenido=True)

    assert r.conoce("viejo")
    # Nace casi vencido: el próximo tic lo da por caído.
    assert r.marcar_caidos(103.0) is True
    assert r.en_linea() == 0


def test_un_latido_de_verdad_revive_al_que_llego_retenido():
    r = RegistroPulsadores(timeout_s=15.0)
    r.alta("p1", 1, 100.0, online=True, retenido=True)
    r.visto("p1", 100.5, online=True, retenido=False)

    assert r.marcar_caidos(110.0) is False      # ya tiene latido fresco
    assert r.en_linea() == 1


def test_un_retenido_tardio_no_pisa_un_latido_fresco():
    r = RegistroPulsadores(timeout_s=15.0)
    r.alta("p1", 1, 100.0)
    r.visto("p1", 110.0)                        # latido real
    r.visto("p1", 111.0, retenido=True)         # retenido que llega después

    assert r.marcar_caidos(120.0) is False
