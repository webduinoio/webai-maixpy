#include <stdio.h>
#include <string.h>

#include "py/runtime.h"
#include "py/mphal.h"
#include "py/mperrno.h"
#include "py/mpconfig.h"
#include "hcsr04.h"
#include "fpioa.h"

#if MAIXPY_PY_MODULES_HCSR04

#define HCSR04_UNIT_CM   0
#define HCSR04_UNIT_INCH 1

const mp_obj_type_t modules_hcsr04_type;

typedef struct {
    mp_obj_base_t         base;
    uint8_t               trig;
    uint8_t               echo;

} modules_hcsr04_obj_t;

mp_obj_t modules_hcsr04_make_new(const mp_obj_type_t *type, size_t n_args, size_t n_kw, const mp_obj_t *all_args) {

    modules_hcsr04_obj_t *self = m_new_obj(modules_hcsr04_obj_t);
    self->base.type = &modules_hcsr04_type;
    enum {
        ARG_trig,
        ARG_echo
    };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_trig,        MP_ARG_REQUIRED|MP_ARG_INT, {.u_int = 6} },
        { MP_QSTR_echo,        MP_ARG_REQUIRED|MP_ARG_INT, {.u_int = 11} }
    };
    mp_map_t kw_args;
    mp_map_init_fixed_table(&kw_args, n_kw, all_args + n_args);
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    mp_arg_parse_all(n_args, all_args, &kw_args,
    MP_ARRAY_SIZE(allowed_args), allowed_args, args);
    if(  (args[ARG_trig].u_int >= FUNC_GPIO0) && (args[ARG_trig].u_int <= FUNC_GPIO7) )
    {
        self->trig = args[ARG_trig].u_int;
    }
    else if( (args[ARG_trig].u_int >= FUNC_GPIOHS0) && (args[ARG_trig].u_int <= FUNC_GPIOHS31) )
    {
        self->trig = args[ARG_trig].u_int;
    }
    else{
        mp_raise_ValueError("trig gpio error");
        return 0;
    }

    if(  (args[ARG_echo].u_int >= FUNC_GPIO0) && (args[ARG_echo].u_int <= FUNC_GPIO7) )
    {
        self->echo = args[ARG_echo].u_int;
    }
    else if( (args[ARG_trig].u_int >= FUNC_GPIOHS0) && (args[ARG_trig].u_int <= FUNC_GPIOHS31) )
    {
        self->echo = args[ARG_echo].u_int;
    }
    else{
        mp_raise_ValueError("echo gpio error");
        return 0;
    }
    return MP_OBJ_FROM_PTR(self);  
}


STATIC void modules_hcsr04_print(const mp_print_t *print, mp_obj_t self_in, mp_print_kind_t kind) {
    modules_hcsr04_obj_t *self = MP_OBJ_TO_PTR(self_in);
    mp_printf(print, "[MAIXPY]hcsr04:(%p) trig=%d\r\n", self, self->trig);
    mp_printf(print, "[MAIXPY]hcsr04:(%p) echo=%d\r\n", self, self->echo);

}

STATIC mp_obj_t modules_hcsr04_measure(size_t n_args, const mp_obj_t *pos_args, mp_map_t *kw_args) {
    enum {
        ARG_unit,
        ARG_timeout,
    };
    static const mp_arg_t allowed_args[] = {
        { MP_QSTR_unit,        MP_ARG_INT, {.u_int = HCSR04_UNIT_CM} },
        { MP_QSTR_timeout,     MP_ARG_INT, {.u_int = 1000000} }
    };
    mp_arg_val_t args[MP_ARRAY_SIZE(allowed_args)];
    long ret;
    modules_hcsr04_obj_t *self = MP_OBJ_TO_PTR(pos_args[0]);

    mp_arg_parse_all(n_args - 1, pos_args + 1, kw_args,
        MP_ARRAY_SIZE(allowed_args), allowed_args, args);
    if(args[ARG_unit].u_int == HCSR04_UNIT_CM)
    {
        ret = hcsr04_measure_cm(self->trig,self->echo, args[ARG_timeout].u_int);
    }
    else
    {
        ret = hcsr04_measure_inch(self->trig,self->echo, args[ARG_timeout].u_int);
    }
    if( ret == -1)
    {
        mp_raise_ValueError("gpio error");
    }
    if( ret == -2)
    {
        mp_raise_ValueError("gpio not register pin");
    }
    if( ret == 0)
        mp_raise_msg(&mp_type_OSError, "time out");
    return mp_obj_new_int(ret);
}
MP_DEFINE_CONST_FUN_OBJ_KW(modules_hcsr04_measure_obj, 1, modules_hcsr04_measure);

STATIC const mp_rom_map_elem_t mp_modules_hcsr04_locals_dict_table[] = {
    { MP_ROM_QSTR(MP_QSTR_measure), MP_ROM_PTR(&modules_hcsr04_measure_obj) },
    { MP_ROM_QSTR(MP_QSTR_UNIT_CM),   MP_ROM_INT(HCSR04_UNIT_CM) },
    { MP_ROM_QSTR(MP_QSTR_UNIT_INCH),   MP_ROM_INT(HCSR04_UNIT_INCH) },
};

MP_DEFINE_CONST_DICT(mp_modules_hcsr04_locals_dict, mp_modules_hcsr04_locals_dict_table);

const mp_obj_type_t modules_hcsr04_type = {
    { &mp_type_type },
    .name = MP_QSTR_hcsr04,
    .print = modules_hcsr04_print,
    .make_new = modules_hcsr04_make_new,
    .locals_dict = (mp_obj_dict_t*)&mp_modules_hcsr04_locals_dict,
};

#endif // MAIXPY_PY_MODULES_HCSR04
