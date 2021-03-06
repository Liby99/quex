/* -*- C++ -*- vim:set syntax=cpp:
 *
 * (C) 2005-2009 Frank-Rene Schaefer                                        */
#ifndef QUEX_INCLUDE_GUARD__EXTRA__ACCUMULATOR__ACCUMULATOR_I
#define QUEX_INCLUDE_GUARD__EXTRA__ACCUMULATOR__ACCUMULATOR_I

$$INC: definitions$$
$$INC: extra/accumulator/Accumulator$$
$$INC: quex/MemoryManager$$

QUEX_NAMESPACE_MAIN_OPEN

QUEX_INLINE void
QUEX_NAME(Accumulator_destruct)(QUEX_NAME(Accumulator)* me);
                      
QUEX_INLINE bool      
QUEX_NAME(Accumulator__extend)(QUEX_NAME(Accumulator)* me, size_t MinAddSize);
                      
QUEX_INLINE void      
QUEX_NAME(Accumulator_print_this)(QUEX_NAME(Accumulator)* me);
                      
QUEX_INLINE bool
QUEX_NAME(Accumulator__flush)(QUEX_NAME(Accumulator)*   me,
                              const QUEX_TYPE_TOKEN_ID  TokenID);
                      
QUEX_INLINE bool
QUEX_NAME(Accumulator__memory_resources_allocate)(QUEX_NAME(Accumulator)*   me);

QUEX_INLINE bool      
QUEX_NAME(Accumulator_construct)(QUEX_NAME(Accumulator)*   me, 
                                 QUEX_TYPE_ANALYZER*       lexer)
{
    me->the_lexer = lexer;

    if( ! QUEX_NAME(Accumulator__memory_resources_allocate)(me) ) {
        QUEX_NAME(Accumulator_resources_absent_mark)(me);
        return false;
    }
        
    $$<count-line>   me->_begin_line   = 0;$$
    $$<count-column> me->_begin_column = 0;$$

$$<C>--------------------------------------------------------------------------
    me->destruct      = QUEX_NAME(Accumulator_destruct);
    me->clear         = QUEX_NAME(Accumulator__clear);
    me->add           = QUEX_NAME(Accumulator__add);
    me->add_character = QUEX_NAME(Accumulator__add_character);
    me->extend        = QUEX_NAME(Accumulator__extend);
    me->flush         = QUEX_NAME(Accumulator__flush);
    me->print_this    = QUEX_NAME(Accumulator_print_this);
$$-----------------------------------------------------------------------------

    return true;
}


QUEX_INLINE void
QUEX_NAME(Accumulator_destruct)(QUEX_NAME(Accumulator)* me)
{
    if( me->text.begin ) {
        QUEX_GNAME_LIB(MemoryManager_free)((void*)me->text.begin,
                                   E_MemoryObjectType_TEXT);
    }
    QUEX_NAME(Accumulator_resources_absent_mark)(me);
}

QUEX_INLINE void
QUEX_NAME(Accumulator_resources_absent_mark)(QUEX_NAME(Accumulator)* me)
{
    me->the_lexer       = 0x0;
    me->text.begin      = 0x0;
    me->text.end        = 0x0;
    me->text.memory_end = 0x0;
}

QUEX_INLINE bool
QUEX_NAME(Accumulator_resources_absent)(QUEX_NAME(Accumulator)* me)
{
    return    me->the_lexer == 0x0 && me->text.begin      == 0x0 
           && me->text.end  == 0x0 && me->text.memory_end == 0x0;
}


QUEX_INLINE bool
QUEX_NAME(Accumulator__memory_resources_allocate)(QUEX_NAME(Accumulator)*   me) 
{
    QUEX_TYPE_LEXATOM* chunk = (QUEX_TYPE_LEXATOM*)0;

    if( QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE ) {
        chunk = (QUEX_TYPE_LEXATOM*)
                QUEX_GNAME_LIB(MemoryManager_allocate)(
                           QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE * sizeof(QUEX_TYPE_LEXATOM),
                           E_MemoryObjectType_TEXT);
        if( ! chunk ) return false;
    }
    me->text.begin      = chunk;
    me->text.end        = me->text.begin;
    me->text.memory_end = &me->text.begin[QUEX_SETTING_ACCUMULATOR_INITIAL_SIZE];
    return true;
}

QUEX_INLINE bool
QUEX_NAME(Accumulator__extend)(QUEX_NAME(Accumulator)* me, size_t MinAddSize)
{
    const size_t  OldContentSize = (size_t)(me->text.end - me->text.begin);
    const size_t  Size    = (size_t)(me->text.memory_end - me->text.begin);
    const size_t  AddSize = (size_t)((float)Size * (float)QUEX_SETTING_ACCUMULATOR_GRANULARITY_FACTOR);
    const size_t  NewSize = Size + (AddSize < MinAddSize ? MinAddSize : AddSize);

    QUEX_TYPE_LEXATOM*  chunk = \
          (QUEX_TYPE_LEXATOM*)
          QUEX_GNAME_LIB(MemoryManager_allocate)(NewSize*sizeof(QUEX_TYPE_LEXATOM),
                                         E_MemoryObjectType_TEXT);

    if( chunk == 0x0 ) return false;

    __quex_assert(me->text.end >= me->text.begin);
    __quex_assert(me->text.memory_end >= me->text.begin);

    QUEX_GSTD(memcpy)(chunk, me->text.begin, sizeof(QUEX_TYPE_LEXATOM) * Size);

    QUEX_GNAME_LIB(MemoryManager_free)((void*)me->text.begin, E_MemoryObjectType_TEXT);

    me->text.begin      = chunk;
    me->text.end        = chunk + OldContentSize;
    me->text.memory_end = chunk + NewSize;
    return true;
}

QUEX_INLINE void
QUEX_NAME(Accumulator__clear)(QUEX_NAME(Accumulator)* me)
{
    me->text.end = me->text.begin;
}

QUEX_INLINE void 
QUEX_NAME(Accumulator__add)(QUEX_NAME(Accumulator)* me,
                           const QUEX_TYPE_LEXATOM* Begin, const QUEX_TYPE_LEXATOM* End)
{ 
    const size_t L = (size_t)(End - Begin);
    __quex_assert(End > Begin);

    /* If it is the first string to be appended, the store the location */
    if( me->text.begin == me->text.end ) {
        $$<count-line>   me->_begin_line   = me->the_lexer->counter._line_number_at_begin;$$
        $$<count-column> me->_begin_column = me->the_lexer->counter._column_number_at_begin;$$
    }

    /* Ensure, that there is one more cell between end and .memory_end to store
     * the terminating zero for flushing or printing.                           */
    if( me->text.memory_end <= me->text.end + L ) {
        /* L + 1 we need space for the string + the terminating zero */
        if( QUEX_NAME(Accumulator__extend)(me, L + 1) == false ) {
            if( me->the_lexer ) {
                QUEX_NAME(MF_error_code_set_if_first)(me->the_lexer, 
                                                      E_Error_Accumulator_OutOfMemory);
                return;
            }
        }
    }

    QUEX_GSTD(memcpy)(me->text.end, Begin, L * sizeof(QUEX_TYPE_LEXATOM));
    me->text.end += L;
}


QUEX_INLINE void 
QUEX_NAME(Accumulator__add_character)(QUEX_NAME(Accumulator)*     me,
                                      const QUEX_TYPE_LEXATOM  Character)
{ 
    /* If it is the first string to be appended, the store the location */
    if( me->text.begin == me->text.end ) {
        $$<count-line>   me->_begin_line   = me->the_lexer->counter._line_number_at_begin;$$
        $$<count-column> me->_begin_column = me->the_lexer->counter._column_number_at_begin;$$
    }

    /* Ensure, that there is one more cell between end and .memory_end to store
     * the terminating zero for flushing or printing.                           */
    if( me->text.memory_end <= me->text.end + 1 ) {
        /* 1 + 1 we need space for the character + the terminating zero */
        if( QUEX_NAME(Accumulator__extend)(me, 2) == false ) {
            if( me->the_lexer ) {
                QUEX_NAME(MF_error_code_set_if_first)(me->the_lexer, 
                                                      E_Error_Accumulator_OutOfMemory);
                return;
            }
        }
    }

    *(me->text.end) = Character;
    ++(me->text.end);
}

QUEX_INLINE bool
QUEX_NAME(Accumulator__flush)(QUEX_NAME(Accumulator)*   me,
                              const QUEX_TYPE_TOKEN_ID  TokenID)
{
    QUEX_TYPE_LEXATOM* begin_p;
    QUEX_TYPE_LEXATOM* end_p;

    if( QUEX_NAME(TokenQueue_is_full)(&me->the_lexer->_token_queue) ) {
        QUEX_NAME(MF_error_code_set_if_first)(me->the_lexer, 
                                              E_Error_Token_QueueOverflow);
        return false;
    }

    /* All functions must ensure: there is one cell to store terminating zero.*/  
    __quex_assert(me->text.end < me->text.memory_end);   

    if( me->text.begin == me->text.end ) {               
        begin_p = &QUEX_GNAME(LexemeNull);
        end_p   = &QUEX_GNAME(LexemeNull);             /* -> terminating zero. */
    }
    else {
        begin_p  = me->text.begin;
        end_p    = me->text.end;
        end_p[0] = (QUEX_TYPE_LEXATOM)0;              /* -> terminating zero. */
    }                                                                              
    /* 'end_p' points *to* terminating zero, *not* behind it.                 */

    /* If no text is to be flushed, behave the same as self_send              */             
    /* That is: self_token_set_id(ID);                                        */             
    /*          QUEX_TOKEN_POLICY_PREPARE_NEXT();                             */             
    /*          BUT: We clear the text of the otherwise void token.           */             
    QUEX_NAME(TokenQueue_push_text)(&me->the_lexer->_token_queue, TokenID, begin_p, end_p);
    QUEX_NAME(Accumulator__clear)(me);                       

    return true;
}

QUEX_INLINE void  
QUEX_NAME(Accumulator_print_this)(QUEX_NAME(Accumulator)* me)
{
    /* All functions must ensure that there is one cell left to store the terminating zero. */


    QUEX_DEBUG_PRINT("  accumulator: ");
    if( ! me->text.end || ! me->text.begin ) {
        QUEX_DEBUG_PRINT("<uninitialized>\n");
    }
    else {
        __quex_assert(me->text.end < me->text.memory_end);
        *(me->text.end) = (QUEX_TYPE_LEXATOM)0; /* see above '__quex_assert()' */
        QUEX_DEBUG_PRINT1("'%s'\n", (const char*)me->text.begin);
    }
}

$$<Cpp>--------------------------------------------------------------------------
QUEX_INLINE 
QUEX_NAME(Accumulator)::QUEX_NAME(Accumulator)()
{ /* C/C++ Compability: Constructors/Destructors do nothing. */ }
                      
QUEX_INLINE 
QUEX_NAME(Accumulator)::~QUEX_NAME(Accumulator)()
{ /* C/C++ Compability: Constructors/Destructors do nothing. */ }
                      
QUEX_INLINE void      
QUEX_NAME(Accumulator)::clear()
{ QUEX_NAME(Accumulator__clear)(this); }
                      
QUEX_INLINE void      
QUEX_NAME(Accumulator)::add(const QUEX_TYPE_LEXATOM* Begin, 
                            const QUEX_TYPE_LEXATOM* End)
{ QUEX_NAME(Accumulator__add)(this, Begin, End); }
                      
QUEX_INLINE void      
QUEX_NAME(Accumulator)::add_character(const QUEX_TYPE_LEXATOM  Lexatom)
{ QUEX_NAME(Accumulator__add_character)(this, Lexatom); }
                      
QUEX_INLINE bool      
QUEX_NAME(Accumulator)::extend(size_t MinAddSize)
{ return QUEX_NAME(Accumulator__extend)(this, MinAddSize); }

QUEX_INLINE bool      
QUEX_NAME(Accumulator)::flush(const QUEX_TYPE_TOKEN_ID TokenID)
{ return QUEX_NAME(Accumulator__flush)(this, TokenID); }
                      
QUEX_INLINE void      
QUEX_NAME(Accumulator)::print_this()
{ QUEX_NAME(Accumulator_print_this)(this); }
$$-----------------------------------------------------------------------------

QUEX_NAMESPACE_MAIN_CLOSE

#endif /* QUEX_INCLUDE_GUARD_EXTRA__ACCUMULATOR__ACCUMULATOR_I */
