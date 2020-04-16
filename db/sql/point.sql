create function point_lt(point, point)
returns boolean language sql immutable as $$
    select $1[0] < $2[0] or $1[0] = $2[0] and $1[1] < $2[1]
$$;

create function point_lte(point, point)
returns boolean language sql immutable as $$
    select point_lt($1, $2) or point_eq($1, $2)
$$;

create function point_gt(point, point)
returns boolean language sql immutable as $$
    select $1[0] > $2[0] or $1[0] = $2[0] and $1[1] > $2[1]
$$;

create function point_gte(point, point)
returns boolean language sql immutable as $$
    select point_gt($1, $2) or point_eq($1, $2)
$$;

create operator =  (leftarg = point, rightarg = point, procedure = point_eq,  commutator = =);
create operator <  (leftarg = point, rightarg = point, procedure = point_lt,  commutator = >);
create operator <= (leftarg = point, rightarg = point, procedure = point_lte, commutator = >=);
create operator >  (leftarg = point, rightarg = point, procedure = point_gt,  commutator = <);
create operator >= (leftarg = point, rightarg = point, procedure = point_gte, commutator = <=);

create function btpointcmp(point, point)
returns integer language sql immutable as $$
    select case 
        when $1 = $2 then 0
        when $1 < $2 then -1
        else 1
    end
$$;

create operator class point_ops
    default for type point using btree as
        operator 1 <,
        operator 2 <=,
        operator 3 =,
        operator 4 >=,
        operator 5 >,
        function 1 btpointcmp(point, point);

CREATE INDEX idx_gin_windows ON NoteWindow USING GIN(normalized);
